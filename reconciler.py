import re
from datetime import datetime
from dateutil import parser
from difflib import SequenceMatcher



def normalize_date(date_input):
    """Parses date formats (ISO strings, '03-15/2025', etc.)."""
    if not date_input or not isinstance(date_input, str):
        return None
    try:
        # Handle formats like '03-15/2025' by replacing slashes
        clean_str = date_input.replace('/', '-')
        return parser.parse(clean_str).date()
    except (ValueError, TypeError):
        # Fallback regex for M-D-YYYY
        m = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', date_input)
        if m:
            month, day, year = m.groups()
            return datetime(int(year), int(month), int(day)).date()
        return None


def text_similarity(str1, str2):
    """Calculates similarity score (0.0 to 1.0) between two strings."""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def extract_domain(email):
    """Extracts company domain from email address."""
    if "@" in email:
        domain = email.split("@")[1].lower()
        return domain.split(".")[0]
    return ""


def calculate_match_score(cal_item, crm_item):
    """
    Scores how likely a Calendar record and CRM record represent the same meeting.
    """
    score = 0.0

    # 1. Date Matching (within 1 day to account for UTC vs local timezone shifts)
    cal_date = normalize_date(cal_item.get("start_time"))
    crm_date = normalize_date(crm_item.get("meeting_date"))

    if cal_date and crm_date:
        days_diff = abs((cal_date - crm_date).days)
        if days_diff == 0:
            score += 0.4
        elif days_diff == 1:
            score += 0.2
        else:
            return 0.0  # Too far apart in time
    else:
        return 0.0

    # 2. Entity Matching (Company / Client / Email Domain)
    crm_company = (crm_item.get("client_company") or "").lower()
    crm_client = (crm_item.get("client_name") or "").lower()
    cal_title = (cal_item.get("title") or "").lower()

    attendees = cal_item.get("attendees", [])
    domains = [extract_domain(email) for email in attendees if extract_domain(email)]

    if crm_company and crm_company in cal_title:
        score += 0.3
    elif any(domain in crm_company or crm_company in domain for domain in domains if domain):
        score += 0.3

    if crm_client and any(crm_client in att.lower() for att in attendees):
        score += 0.2

    # 3. Title / Subject Similarity
    title_sim = text_similarity(cal_item.get("title"), crm_item.get("subject"))
    score += title_sim * 0.2

    return score


def deduplicate_records(records, id_field):
    """Removes exact duplicate entries within a single source."""
    seen = set()
    unique = []
    for record in records:
        rec_id = record.get(id_field)
        if rec_id and rec_id not in seen:
            seen.add(rec_id)
            unique.append(record)
        elif not rec_id:
            unique.append(record)
    return unique


def reconcile_meetings(calendar_data, crm_data):
    """
    Reconciles calendar records and CRM records into a unified list.
    """
    cal_clean = deduplicate_records(calendar_data or [], "event_id")
    crm_clean = deduplicate_records(crm_data or [], "crm_id")

    matched_crm_ids = set()
    unified_meetings = []

    for cal in cal_clean:
        best_match = None
        best_score = 0.0

        for crm in crm_clean:
            if crm.get("crm_id") in matched_crm_ids:
                continue

            score = calculate_match_score(cal, crm)
            if score > best_score and score >= 0.5:
                best_score = score
                best_match = crm

        if best_match:
            matched_crm_ids.add(best_match["crm_id"])
            unified_meetings.append(merge_records(cal, best_match))
        else:
            unified_meetings.append(format_calendar_only(cal))

    # Add remaining CRM-only records
    for crm in crm_clean:
        if crm.get("crm_id") not in matched_crm_ids:
            unified_meetings.append(format_crm_only(crm))

    return unified_meetings


def merge_records(cal, crm):
    cal_date = normalize_date(cal.get("start_time"))
    crm_date = normalize_date(crm.get("meeting_date"))

    # Resolve missing client info
    client_info = resolve_client_info(
        crm_name=crm.get("client_name"),
        crm_company=crm.get("client_company"),
        attendees=cal.get("attendees", []),
        meeting_type=crm.get("meeting_type")
    )

    return {
        "unified_id": f"UNI-{cal.get('event_id')}-{crm.get('crm_id')}",
        "title": cal.get("title") or crm.get("subject"),
        "client": client_info,  # <--- Validated client object
        "organizer": cal.get("organizer") or crm.get("relationship_owner"),
        "attendees": cal.get("attendees", []),
        "date": (cal_date or crm_date).isoformat() if (cal_date or crm_date) else None,
        "time": {
            "calendar_start": cal.get("start_time"),
            "calendar_end": cal.get("end_time"),
            "crm_time": crm.get("meeting_time")
        },
        "location": {
            "calendar_location": cal.get("location"),
            "crm_location": crm.get("location"),
            "crm_meeting_type": crm.get("meeting_type"),
            "resolved_location": crm.get("location") or cal.get("location")
        },
        "status": cal.get("status") or crm.get("status"),
        "notes": crm.get("notes") or cal.get("description"),
        "sources": {
            "calendar_id": cal.get("event_id"),
            "crm_id": crm.get("crm_id")
        }
    }


def format_calendar_only(cal):
    cal_date = normalize_date(cal.get("start_time"))
    return {
        "unified_id": f"UNI-{cal.get('event_id')}",
        "title": cal.get("title"),
        "client": {"name": None, "company": None},
        "organizer": cal.get("organizer"),
        "attendees": cal.get("attendees", []),
        "date": cal_date.isoformat() if cal_date else None,
        "time": {
            "calendar_start": cal.get("start_time"),
            "calendar_end": cal.get("end_time"),
            "crm_time": None
        },
        "location": {
            "calendar_location": cal.get("location"),
            "crm_location": None,
            "crm_meeting_type": None,
            "resolved_location": cal.get("location")
        },
        "status": cal.get("status"),
        "notes": cal.get("description"),
        "sources": {
            "calendar_id": cal.get("event_id"),
            "crm_id": None
        }
    }


def format_crm_only(crm):
    crm_date = normalize_date(crm.get("meeting_date"))
    return {
        "unified_id": f"UNI-{crm.get('crm_id')}",
        "title": crm.get("subject"),
        "client": {
            "name": crm.get("client_name"),
            "company": crm.get("client_company")
        },
        "organizer": crm.get("relationship_owner"),
        "attendees": [],
        "date": crm_date.isoformat() if crm_date else None,
        "time": {
            "calendar_start": None,
            "calendar_end": None,
            "crm_time": crm.get("meeting_time")
        },
        "location": {
            "calendar_location": None,
            "crm_location": crm.get("location"),
            "crm_meeting_type": crm.get("meeting_type"),
            "resolved_location": crm.get("location")
        },
        "status": crm.get("status"),
        "notes": crm.get("notes"),
        "sources": {
            "calendar_id": None,
            "crm_id": crm.get("crm_id")
        }
    }


def resolve_client_info(crm_name, crm_company, attendees=None, meeting_type=None):
    """Fallback handler for missing client details."""
    name = crm_name
    company = crm_company

    # Check for internal meetings
    is_internal = meeting_type == "Internal"
    if attendees and not is_internal:
        is_internal = all("@firma.com" in a.lower() for a in attendees)

    if is_internal:
        return {
            "name": name or "Internal Team",
            "company": company or "Internal"
        }

    return {
        "name": name or "Not Specified",
        "company": company or "N/A"
    }