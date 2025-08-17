def suggestions(section_map: dict, skills_found: list, missing_keywords: list):
    msgs = []
    if not section_map.get("summary"):
        msgs.append("Add a brief **Summary/Objective** with your target role and 2–3 achievements.")
    if not section_map.get("projects"):
        msgs.append("Include **2–3 key projects** with tech stack, your role, and measurable outcomes.")
    if not section_map.get("achievements"):
        msgs.append("List **Achievements** with numbers (e.g., improved X by Y%).")
    if missing_keywords:
        msgs.append(f"Missing **ATS keywords** from JD: {', '.join(missing_keywords[:15])} …")
    if not skills_found:
        msgs.append("Populate the **Skills** section with tools/libraries you actually used.")
    return msgs
