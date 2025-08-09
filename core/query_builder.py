from typing import List


def build_expert_query(
    full_text: str = None,
    notice_type: str = None,
    cpv: str = None,
    place_of_performance: str = None,
    contract_type: str = None,
    value_min: int = None,
    value_max: int = None,
    pub_date_from: str = None,
    pub_date_to: str = None,
    deadline_from: str = None,
    deadline_to: str = None,
    buyer_name: str = None,
    buyer_town: str = None,
    buyer_country: str = None,
    buyer_type: str = None,
    authority_activity: str = None,
) -> str:
    """Build TED API expert query from simplified parameters.
    Behaviour preserved from UI implementation.
    """
    parts: List[str] = []

    # 1. Free text search
    if full_text and full_text.strip():
        parts.append(f'FT~("{full_text.strip()}")')

    # 2. Notice type (business opportunities)
    if notice_type:
        parts.append(f'NT="{notice_type}"')

    # 3. CPV code (business section)
    if cpv and cpv.strip():
        parts.append(f'PC="{cpv.strip()}"')

    # 4. Place of performance (where the work will be done)
    if place_of_performance and place_of_performance.strip():
        parts.append(f'RC="{place_of_performance.strip()}"')

    # 5. Contract type (nature of contract)
    if contract_type:
        parts.append(f'NC="{contract_type}"')

    # 5. Procurement value
    if value_min is not None and value_max is not None:
        parts.append(f'VR=[{value_min} TO {value_max}]')
    elif value_min is not None:
        parts.append(f'VR>={value_min}')
    elif value_max is not None:
        parts.append(f'VR<={value_max}')

    # 6. Publication date
    if pub_date_from and pub_date_to:
        # Use separate >= and <= operators instead of TO syntax
        parts.append(f'PD>={pub_date_from}')
        parts.append(f'PD<={pub_date_to}')
    elif pub_date_from:
        parts.append(f'PD>={pub_date_from}')
    elif pub_date_to:
        parts.append(f'PD<={pub_date_to}')

    # 7. Deadline
    if deadline_from and deadline_to:
        # Use separate >= and <= operators instead of TO syntax
        parts.append(f'DD>={deadline_from}')
        parts.append(f'DD<={deadline_to}')
    elif deadline_from:
        parts.append(f'DD>={deadline_from}')
    elif deadline_to:
        parts.append(f'DD<={deadline_to}')

    # 8. Buyer information
    if buyer_name and buyer_name.strip():
        parts.append(f'AU~("{buyer_name.strip()}")')

    if buyer_town and buyer_town.strip():
        parts.append(f'buyer-town~("{buyer_town.strip()}")')

    if buyer_country:
        parts.append(f'CY="{buyer_country}"')  # Use CY for country

    if buyer_type:
        parts.append(f'buyer-type="{buyer_type}"')

    if authority_activity:
        parts.append(f'authority-main-activity="{authority_activity}"')

    # If no conditions specified, return empty query (this shouldn't happen with default dates)
    if not parts:
        # This should not happen since we have default publication dates
        print("WARNING - No search criteria specified, this should not happen!")
        return ""

    return ' AND '.join(parts)
