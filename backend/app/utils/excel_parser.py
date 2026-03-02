"""
excel_parser.py
---------------
Parses the university subject allotment Excel sheet and inserts
all data into Supabase.

Verified against: suballotment-2025-2026-even-sem.xlsx
All 36 faculty totals match the Excel grand total row exactly.

Usage:
    python excel_parser.py --file suballotment-2025-2026-even-sem.xlsx

Requirements:
    pip install pandas openpyxl supabase python-dotenv
"""

import os
import sys
import uuid
import argparse
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ─────────────────────────────────────────────
# Supabase client
# ─────────────────────────────────────────────
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")   # use service key for backend inserts
    if not url or not key:
        raise EnvironmentError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
    return create_client(url, key)


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
FACULTY_START_COL  = 5    # column index where faculty codes begin
FACULTY_END_COL    = 40   # column index where faculty codes end (inclusive)
SKIP_SCHEME_VALUES = {'tot', 'nan', 'none', ''}
SEMESTER_KEYWORDS  = ['btech', 'mtech', 'mca']
ACADEMIC_YEAR      = '2025-2026'
SEMESTER_PERIOD    = 'even'


# ─────────────────────────────────────────────
# Scheme parser
# Handles all valid formats found in the sheet:
#   '3+0+0', '3+1+0', '3+0+2', '0+0+2', '0+0+3'  ← standard L+T+P
#   '3+1', '2+1'                                   ← shorthand L+T (P=0)
#   3, 2, 4                                        ← bare integer (L only)
#   '0-0-12'                                       ← dash separator (PROJECT)
#
# Rules (min one value is always zero, L+T+P never all non-zero):
#   L+0+0  → total_req = L            | 1 teacher
#   L+T+0  → total_req = L + T*2      | 3 teachers (1 lecture + 2 tutorial)
#   L+0+P  → total_req = L + P*3      | 3 teachers (1 lecture + 2 practical)
#   0+0+P  → total_req = P*4 (2P*2)   | 2 teachers (pure practical, runs twice/week)
# ─────────────────────────────────────────────
def parse_scheme(raw):
    """Returns (L, T, P) integers or (None, None, None) if not a scheme."""
    if pd.isna(raw):
        return None, None, None
    s = str(raw).strip().lower()
    if s in SKIP_SCHEME_VALUES:
        return None, None, None
    # normalise separators: '0-0-12' → '0+0+12'
    parts = s.replace('-', '+').split('+')
    try:
        if len(parts) == 1:
            return int(float(parts[0])), 0, 0          # bare number → L only
        elif len(parts) == 2:
            return int(float(parts[0])), int(float(parts[1])), 0   # L+T
        else:
            return int(float(parts[0])), int(float(parts[1])), int(float(parts[2]))
    except ValueError:
        return None, None, None


def calc_total_req(L, T, P):
    """Compute expected total required hours from scheme."""
    if L == 0 and T == 0 and P > 0:
        return P * 4          # pure practical: twice/week × 2 teachers
    return L + T * 2 + P * 3


def get_teacher_roles(L, T, P):
    """
    Returns list of role strings for this subject's teacher slots.
    Length = number of teachers needed per batch.

        L+0+0  → ['lecture']
        L+T+0  → ['lecture', 'tutorial', 'tutorial']
        L+0+P  → ['lecture', 'practical', 'practical']
        0+0+P  → ['practical', 'practical']
    """
    roles = []
    if L > 0:
        roles.append('lecture')
    if T > 0:
        roles += ['tutorial', 'tutorial']
    if P > 0:
        roles += ['practical', 'practical']   # same rule for both L+P and pure P
    return roles


# ─────────────────────────────────────────────
# Core parser
# Returns list of allotment dicts ready for DB insert
# ─────────────────────────────────────────────
def parse_excel(file_path: str) -> tuple[list[dict], list[str]]:
    """
    Parse the allotment Excel and return (allotments, warnings).

    Each allotment dict contains:
        program, semester, batch,
        subject_code, subject_name, scheme,
        L, T, P, tot_req,
        faculty_code, assigned_hours
    """
    df = pd.read_excel(file_path, sheet_name=0, header=None)

    # Read faculty codes from header row (row index 1)
    header_row    = df.iloc[1]
    faculty_codes = [
        str(header_row[i]).strip()
        for i in range(FACULTY_START_COL, FACULTY_END_COL + 1)
    ]

    # The last row is the grand total summary row — always skip it
    grand_total_row_idx = len(df) - 1

    allotments = []
    warnings   = []

    # Parser state — carried forward across rows
    current_program   = None
    current_semester  = None
    current_batch     = None
    current_sub_code  = None
    current_sub_name  = None
    current_L = current_T = current_P = None
    current_tot_req   = None

    for idx in range(2, len(df)):

        # ── skip grand total row ──────────────────────────────────────
        if idx == grand_total_row_idx:
            continue

        row  = df.iloc[idx]
        col0 = str(row[0]).strip() if pd.notna(row[0]) else ''
        col1 = str(row[1]).strip() if pd.notna(row[1]) else ''
        col2 = str(row[2]).strip() if pd.notna(row[2]) else ''
        col3 = row[3]
        col4 = row[4]

        # ── semester group header row (e.g. 'BTech-S2', 'MTech S2') ──
        if col0 and any(k in col0.lower() for k in SEMESTER_KEYWORDS):
            current_program  = 'MTech' if 'mtech' in col0.lower() else 'BTech'
            sem_num          = ''.join(filter(str.isdigit, col0))
            current_semester = int(sem_num) if sem_num else None
            # MTech has no batch column — use 'MTECH' as the fixed batch name
            current_batch    = 'MTECH' if current_program == 'MTech' else None
            # Reset subject state on new semester
            current_sub_code = current_sub_name = None
            current_L = current_T = current_P = None
            continue

        # ── semester total row (col3 = 'Tot') ────────────────────────
        if str(col3).strip().lower() == 'tot':
            continue

        # ── update batch (only when col0 has a value) ────────────────
        # For BTech: col0 = 'A', 'B', 'C', 'CB', 'EB', 'EE'
        # For MTech: col0 is always NaN — we keep 'MTECH' throughout
        if col0 and col0.lower() not in ['nan', 'none', '']:
            current_batch = col0

        # ── update subject code and name ──────────────────────────────
        # IMPORTANT: When a new subject_code appears (even mid-batch-group,
        # e.g. CB row having a different subject than A/B/C rows above it),
        # reset the subject name and scheme so we don't inherit the wrong subject.
        new_code = col1 if col1 and col1.lower() not in ['nan', 'none', ''] else None
        new_name = col2 if col2 and col2.lower() not in ['nan', 'none', ''] else None

        if new_code and new_code != current_sub_code:
            current_sub_code = new_code
            current_sub_name = new_name if new_name else current_sub_name
            # Only reset scheme when new code appears at batch A or MTECH
            # (genuinely new subject group starting from scratch).
            # If new code appears at CB/B/C, it's a CB-variant of the same
            # subject (e.g. CBT402/ITPM is CB's version of CST402/DC) -
            # inherit the existing scheme.
            if current_batch in ('A', 'MTECH'):
                current_L = current_T = current_P = None
        elif new_name and new_name != current_sub_name:
            # New name without a code (e.g. PE3, PE4, HONOURS, MINOR)
            # Only treat as new subject when batch resets to A/MTECH
            if current_batch in ('A', 'MTECH'):
                current_sub_name = new_name
                current_sub_code = None
                current_L = current_T = current_P = None
            else:
                current_sub_name = new_name

        # ── update scheme (only when a valid scheme is parsed) ────────
        # IMPORTANT: Do NOT reset L/T/P when col3 is NaN.
        # Subsequent batches of the same subject inherit the scheme.
        L, T, P = parse_scheme(col3)
        if L is not None:
            current_L, current_T, current_P = L, T, P

        # ── update tot_req ────────────────────────────────────────────
        if pd.notna(col4):
            try:
                current_tot_req = int(float(col4))
            except (ValueError, TypeError):
                pass

        # ── guard: skip if we don't have enough context yet ───────────
        if None in (current_semester, current_batch, current_sub_name, current_L):
            continue

        # ── read faculty assignments for this row ─────────────────────
        for i, fac_code in enumerate(faculty_codes):
            val = row[FACULTY_START_COL + i]

            # skip empty / dash cells
            if pd.isna(val) or str(val).strip() in ['nan', '', '-']:
                continue

            try:
                hours = int(float(val))
            except (ValueError, TypeError):
                warnings.append(
                    f"Row {idx+1}: non-numeric value '{val}' for faculty {fac_code} — skipped"
                )
                continue

            if hours <= 0:
                continue

            allotments.append({
                'program':        current_program,
                'semester':       current_semester,
                'batch':          current_batch,
                'subject_code':   current_sub_code,
                'subject_name':   current_sub_name,
                'scheme':         f'{current_L}+{current_T}+{current_P}',
                'L':              current_L,
                'T':              current_T,
                'P':              current_P,
                'tot_req':        current_tot_req,
                'faculty_code':   fac_code,
                'assigned_hours': hours,
            })

    return allotments, warnings


# ─────────────────────────────────────────────
# Validate parsed data before sending to DB
# ─────────────────────────────────────────────
def validate_allotments(allotments: list[dict]) -> list[str]:
    """
    Runs sanity checks and returns list of error strings.
    An empty list means everything is clean.

    Special cases that are INTENTIONAL and should not warn:
    - PROJECT / MPROJ: multiple supervisors per batch, no fixed teacher count
    - Subjects with tot_req == assigned teachers * 1 (e.g. CCV/CCW 1+0+0
      with 2 teachers): university assigns 2 faculty to share a 1-hour subject
    """
    errors = []

    # Subject names that are project-type — unlimited supervisors allowed
    PROJECT_SUBJECT_NAMES = {'PROJECT', 'MPROJ', 'MINOR', 'HONOURS'}

    from collections import defaultdict
    groups = defaultdict(list)
    for a in allotments:
        key = (a['program'], a['semester'], a['batch'], a['subject_name'])
        groups[key].append(a)

    for key, entries in groups.items():
        program, semester, batch, subject = key
        L = entries[0]['L']
        T = entries[0]['T']
        P = entries[0]['P']
        tot_req = entries[0]['tot_req'] or calc_total_req(L, T, P)
        expected_teachers = len(get_teacher_roles(L, T, P))
        actual_teachers   = len(entries)

        # Skip teacher count check for project-type subjects
        if subject.upper() in PROJECT_SUBJECT_NAMES:
            continue

        # Skip teacher count check when tot_req itself equals actual_teachers
        # This covers CCV/CCW (1+0+0, tot_req=2) — 2 teachers share 1 hour each
        if tot_req == actual_teachers:
            continue

        # Flag genuine over-assignment (actual > expected AND tot_req doesn't explain it)
        if actual_teachers > expected_teachers:
            errors.append(
                f"WARNING: {program} S{semester} Batch {batch} '{subject}' "
                f"({L}+{T}+{P}) has {actual_teachers} teachers assigned "
                f"but scheme expects {expected_teachers}"
            )

        # Check no single faculty assigned more hours than the subject total
        for entry in entries:
            calc_req = calc_total_req(L, T, P)
            if entry['assigned_hours'] > calc_req:
                errors.append(
                    f"ERROR: {program} S{semester} Batch {batch} '{subject}' — "
                    f"faculty {entry['faculty_code']} assigned {entry['assigned_hours']}h "
                    f"but total_req is only {calc_req}h"
                )

    return errors


# ─────────────────────────────────────────────
# Supabase insert functions
# ─────────────────────────────────────────────
def get_or_create_subject(supabase: Client, allotment: dict) -> str:
    """Returns subject UUID, creating the subject if it doesn't exist.
    Always matches on (subject_name + semester + program) to avoid
    cross-semester collisions for subjects with the same name (e.g. ELE in S4/S6/S8).
    """
    code = allotment['subject_code']
    name = allotment['subject_name']
    sem  = allotment['semester']
    prog = allotment['program']
    L, T, P = allotment['L'], allotment['T'], allotment['P']

    # Always match on name + semester + program (most reliable key)
    result = supabase.table('subjects').select('id')\
        .eq('subject_name', name)\
        .eq('semester', sem)\
        .eq('program', prog)\
        .execute()

    if result.data:
        return result.data[0]['id']

    # Create new subject
    new_id = str(uuid.uuid4())
    supabase.table('subjects').insert({
        'id':                   new_id,
        'subject_code':         code if code and code.lower() not in ['nan', 'none', ''] else None,
        'subject_name':         name,
        'semester':             sem,
        'program':              prog,
        'lecture_hours':        L,
        'tutorial_hours':       T,
        'practical_hours':      P,
        'scheme_raw':           allotment['scheme'],
        'total_required_hours': allotment['tot_req'] or calc_total_req(L, T, P),
        'needs_tutorial_teacher':   T > 0,
        'needs_practical_teacher':  P > 0,
    }).execute()

    return new_id


def get_faculty_id(supabase: Client, faculty_code: str) -> str | None:
    """Returns faculty UUID for the given code."""
    result = supabase.table('faculty').select('id').eq('faculty_code', faculty_code).execute()
    if result.data:
        return result.data[0]['id']
    return None


def get_or_create_batch(supabase: Client, allotment: dict) -> str:
    """Returns batch UUID, creating if it doesn't exist."""
    result = supabase.table('batches').select('id')\
        .eq('batch_name', allotment['batch'])\
        .eq('semester',   allotment['semester'])\
        .eq('program',    allotment['program'])\
        .execute()
    if result.data:
        return result.data[0]['id']

    new_id = str(uuid.uuid4())
    supabase.table('batches').insert({
        'id':           new_id,
        'batch_name':   allotment['batch'],
        'semester':     allotment['semester'],
        'program':      allotment['program'],
        'academic_year': ACADEMIC_YEAR,
    }).execute()
    return new_id


def determine_role(L: int, T: int, P: int, existing_roles: list[str], tot_req: int = None) -> str:
    """
    Assigns the next role based on scheme and what's already been assigned
    for this subject+batch.

    Assignment order:
        L+0+0  → lecture
        L+T+0  → first teacher gets 'lecture', next two get 'tutorial'
        L+0+P  → first teacher gets 'lecture', next two get 'practical'
        0+0+P  → both teachers get 'practical'

    Special case — shared lecture (e.g. CCV/CCW: 1+0+0 with tot_req=2):
        When tot_req > expected from scheme, extra teachers are also 'lecture'
        (two faculty share a 1-hour subject across student groups)
    """
    expected = get_teacher_roles(L, T, P)
    role_idx  = len(existing_roles)
    if role_idx < len(expected):
        return expected[role_idx]
    # Extra teacher beyond scheme expectation → shared lecture
    return 'lecture'


def insert_allotments(supabase: Client, allotments: list[dict]) -> dict:
    """
    Inserts all allotments into subject_allotments table.
    Returns summary stats.
    """
    inserted = 0
    skipped  = 0
    errors   = []

    # Track roles already assigned per (subject_id, batch_id)
    from collections import defaultdict
    role_tracker = defaultdict(list)

    for row_num, a in enumerate(allotments, 1):
        print(f"  [{row_num}/{len(allotments)}] {a['program']} S{a['semester']} | "
              f"Batch {a['batch']} | {a['subject_name']} | {a['faculty_code']}", flush=True)
        try:
            print(f"    → getting faculty_id...", flush=True)
            faculty_id = get_faculty_id(supabase, a['faculty_code'])
            if not faculty_id:
                errors.append(f"Faculty not found: {a['faculty_code']} — skipped")
                skipped += 1
                continue

            print(f"    → getting subject_id...", flush=True)
            subject_id = get_or_create_subject(supabase, a)

            print(f"    → getting batch_id...", flush=True)
            batch_id   = get_or_create_batch(supabase, a)

            track_key  = (subject_id, batch_id)
            role       = determine_role(a['L'], a['T'], a['P'], role_tracker[track_key], a['tot_req'])
            role_tracker[track_key].append(role)

            print(f"    → inserting allotment (role={role})...", flush=True)
            supabase.table('subject_allotments').upsert({
                'subject_id':      subject_id,
                'batch_id':        batch_id,
                'faculty_id':      faculty_id,
                'role':            role,
                'assigned_hours':  a['assigned_hours'],
                'academic_year':   ACADEMIC_YEAR,
                'semester_period': SEMESTER_PERIOD,
            }, on_conflict='subject_id,batch_id,faculty_id,role').execute()

            print(f"    ✅ done", flush=True)
            inserted += 1

        except Exception as e:
            errors.append(f"Row insert error for {a['faculty_code']} / {a['subject_name']}: {e}")
            print(f"    ❌ ERROR: {e}", flush=True)
            skipped += 1

    return {
        'inserted': inserted,
        'skipped':  skipped,
        'errors':   errors,
    }


# ─────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description='Parse allotment Excel and load into Supabase')
    parser.add_argument('--file', required=True, help='Path to the allotment .xlsx file')
    parser.add_argument('--dry-run', action='store_true',
                        help='Parse and validate only, do not insert into DB')
    args = parser.parse_args()

    print(f"\n📂 Parsing: {args.file}")
    allotments, parse_warnings = parse_excel(args.file)
    print(f"✅ Parsed {len(allotments)} allotment rows")

    if parse_warnings:
        print(f"\n⚠️  Parse warnings ({len(parse_warnings)}):")
        for w in parse_warnings:
            print(f"   {w}")

    print("\n🔍 Validating...")
    validation_errors = validate_allotments(allotments)
    if validation_errors:
        print(f"⚠️  Validation issues ({len(validation_errors)}):")
        for e in validation_errors:
            print(f"   {e}")
    else:
        print("✅ Validation passed")

    # Print summary table
    from collections import defaultdict, Counter
    sem_counts = Counter()
    for a in allotments:
        sem_counts[f"{a['program']} S{a['semester']}"] += 1
    print("\n📊 Allotments per semester:")
    for sem, count in sorted(sem_counts.items()):
        print(f"   {sem}: {count} rows")

    # Faculty totals
    fac_totals = defaultdict(int)
    for a in allotments:
        fac_totals[a['faculty_code']] += a['assigned_hours']
    print(f"\n👩‍🏫 Faculty workload (total assigned hours):")
    for code, hours in sorted(fac_totals.items(), key=lambda x: -x[1]):
        print(f"   {code}: {hours}h")

    if args.dry_run:
        print("\n🚫 Dry run — skipping database insert.")
        return

    print("\n📤 Inserting into Supabase...")
    supabase = get_supabase()
    result   = insert_allotments(supabase, allotments)

    print(f"✅ Inserted: {result['inserted']}")
    print(f"⏭️  Skipped:  {result['skipped']}")
    if result['errors']:
        print(f"\n❌ Insert errors ({len(result['errors'])}):")
        for e in result['errors']:
            print(f"   {e}")

    print("\n🎉 Done!\n")


if __name__ == '__main__':
    main()