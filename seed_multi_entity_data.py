"""
Multi-Entity Sample Data Seeder
================================
Seeds the multi-entity management system with demo data including:
- MMD Group Holdings (parent group)
- SDAD Auto Spare Parts Trading LLC
- AFRA Auto Spare Parts Trading FZCO
- Carmania General Trading LLC
- Multiple branches and sites
- Sample relationships and access assignments
"""

from multi_entity_models import (
    run_migrations, get_db,
    get_all_groups, get_all_entities,
    create_group, create_entity, create_branch, create_site,
    create_relationship, assign_entity_access,
    create_numbering_scheme, create_intercompany_rule,
    get_entity_by_id, get_group_by_id
)


def seed_multi_entity_data():
    """Seed multi-entity demo data."""
    print("Running multi-entity migrations...")
    run_migrations()

    print("Seeding multi-entity sample data...")

    # Create Groups
    print("Creating groups...")
    group_data = {
        'group_code': 'MMD-GROUP',
        'legal_name': 'MMD Group Holdings',
        'trade_name': 'MMD Group',
        'short_name': 'MMD',
        'group_type': 'holding',
        'registration_number': 'GR-2020-0001',
        'tax_identification': 'TAX-GR-2020-0001',
        'vat_number': 'VAT-GR-2020-0001',
        'country': 'UAE',
        'state_region': 'Dubai',
        'city': 'Dubai',
        'address_line1': 'Business Bay, Executive Tower H',
        'postal_code': '12345',
        'phone': '+971-4-123-4567',
        'mobile': '+971-50-123-4567',
        'email': 'info@mmdgroup.ae',
        'website': 'https://mmdgroup.ae',
        'default_currency': 'AED',
        'fiscal_year_start': 1,
        'fiscal_year_end': 12,
        'base_language': 'en',
        'is_active': 1,
        'notes': 'Main holding company for MMD Group',
        'created_by': 1
    }

    try:
        group_id = create_group(group_data)
        print(f"  Created group: MMD Group Holdings (ID: {group_id})")
    except Exception as e:
        print(f"  Group may already exist: {e}")
        # Get existing group
        groups = get_all_groups()
        existing = next((g for g in groups if g['group_code'] == 'MMD-GROUP'), None)
        group_id = existing['id'] if existing else None

    if not group_id:
        print("  Could not create or find group, skipping entity creation")
        return

    # Create Legal Entities
    print("Creating legal entities...")

    entities = [
        {
            'entity_code': 'SDAD',
            'legal_name': 'SDAD Auto Spare Parts Trading LLC',
            'short_name': 'SDAD',
            'trade_name': 'SDAD Auto Parts',
            'entity_type': 'subsidiary',
            'business_type': 'Trading',
            'registration_number': 'TR-2015-SDAD-001',
            'tax_identification': 'TAX-SDAD-2015',
            'vat_number': 'VAT-SDAD-10001',
            'license_number': 'L-123456',
            'license_type': 'Trading License',
            'country': 'UAE',
            'state_region': 'Dubai',
            'city': 'Dubai',
            'district': 'Deira',
            'address_line1': 'Al Muraqqabat Road',
            'address_line2': 'Deira',
            'postal_code': '23456',
            'phone': '+971-4-234-5678',
            'mobile': '+971-50-234-5678',
            'email': 'info@sdad.ae',
            'website': 'https://sdad.ae',
            'default_currency': 'AED',
            'timezone': 'Asia/Dubai',
            'date_format': 'DD/MM/YYYY',
            'fiscal_year_start': 1,
            'fiscal_year_end': 12,
            'base_language': 'en',
            'ownership_percentage': 100,
            'parent_group_id': group_id,
            'intercompany_partner_code': 'IC-SDAD-001',
            'consolidation_flag': 1,
            'is_active': 1,
            'status': 'active',
            'primary_contact_name': 'Ahmed Al Maktoum',
            'primary_contact_email': 'ahmed@sdad.ae',
            'primary_contact_phone': '+971-50-234-5678',
            'finance_contact_name': 'Fatima Hassan',
            'finance_contact_email': 'fatima@sdad.ae',
            'document_prefix': 'SDAD',
            'notes': 'Primary auto spare parts trading entity in Dubai',
            'created_by': 1
        },
        {
            'entity_code': 'AFRA',
            'legal_name': 'AFRA Auto Spare Parts Trading FZCO',
            'short_name': 'AFRA',
            'trade_name': 'AFRA Autoparts',
            'entity_type': 'subsidiary',
            'business_type': 'Trading',
            'registration_number': 'TR-2018-AFRA-001',
            'tax_identification': 'TAX-AFRA-2018',
            'vat_number': 'VAT-AFRA-10002',
            'license_number': 'L-789012',
            'license_type': 'Free Zone License',
            'country': 'UAE',
            'state_region': 'Dubai',
            'city': 'Dubai',
            'district': 'JAFZA',
            'address_line1': 'Jebel Ali Free Zone',
            'address_line2': 'Plot No. JAFZA-1234',
            'postal_code': '34567',
            'phone': '+971-4-345-6789',
            'mobile': '+971-50-345-6789',
            'email': 'info@afra.ae',
            'website': 'https://afra.ae',
            'default_currency': 'AED',
            'timezone': 'Asia/Dubai',
            'date_format': 'DD/MM/YYYY',
            'fiscal_year_start': 1,
            'fiscal_year_end': 12,
            'base_language': 'en',
            'ownership_percentage': 100,
            'parent_group_id': group_id,
            'intercompany_partner_code': 'IC-AFRA-001',
            'consolidation_flag': 1,
            'is_active': 1,
            'status': 'active',
            'primary_contact_name': 'Khalid Al Rashid',
            'primary_contact_email': 'khalid@afra.ae',
            'primary_contact_phone': '+971-50-345-6789',
            'finance_contact_name': 'Sara Mohammed',
            'finance_contact_email': 'sara@afra.ae',
            'document_prefix': 'AFRA',
            'notes': 'JAFZA-based free zone entity for export operations',
            'created_by': 1
        },
        {
            'entity_code': 'CARM',
            'legal_name': 'Carmania General Trading LLC',
            'short_name': 'Carmania',
            'trade_name': 'Carmania Trading',
            'entity_type': 'subsidiary',
            'business_type': 'General Trading',
            'registration_number': 'TR-2020-CARM-001',
            'tax_identification': 'TAX-CARM-2020',
            'vat_number': 'VAT-CARM-10003',
            'license_number': 'L-567890',
            'license_type': 'General Trading License',
            'country': 'UAE',
            'state_region': 'Abu Dhabi',
            'city': 'Abu Dhabi',
            'district': 'Khalifa City',
            'address_line1': 'Khalifa City, Street 12',
            'postal_code': '45678',
            'phone': '+971-2-456-7890',
            'mobile': '+971-50-456-7890',
            'email': 'info@carmania.ae',
            'website': 'https://carmania.ae',
            'default_currency': 'AED',
            'timezone': 'Asia/Dubai',
            'date_format': 'DD/MM/YYYY',
            'fiscal_year_start': 1,
            'fiscal_year_end': 12,
            'base_language': 'en',
            'ownership_percentage': 60,
            'parent_group_id': group_id,
            'intercompany_partner_code': 'IC-CARM-001',
            'consolidation_flag': 1,
            'is_active': 1,
            'status': 'active',
            'primary_contact_name': 'Omar Al Nuaimi',
            'primary_contact_email': 'omar@carmania.ae',
            'primary_contact_phone': '+971-50-456-7890',
            'finance_contact_name': 'Layla Ahmed',
            'finance_contact_email': 'layla@carmania.ae',
            'document_prefix': 'CARM',
            'notes': 'General trading entity in Abu Dhabi, 60% owned',
            'created_by': 1
        }
    ]

    entity_ids = {}
    for entity_data in entities:
        try:
            entity_id = create_entity(entity_data)
            entity_ids[entity_data['entity_code']] = entity_id
            print(f"  Created entity: {entity_data['legal_name']} (ID: {entity_id})")
        except Exception as e:
            print(f"  Entity may already exist: {e}")
            # Try to get existing
            all_ents = get_all_entities()
            existing = next((e for e in all_ents if e['entity_code'] == entity_data['entity_code']), None)
            if existing:
                entity_ids[entity_data['entity_code']] = existing['id']

    # Create Branches
    print("Creating branches...")

    branches = [
        {
            'entity_id': entity_ids.get('SDAD'),
            'branch_code': 'SDAD-HQ',
            'branch_name': 'SDAD Deira HQ',
            'short_name': 'Deira HQ',
            'branch_type': 'head_office',
            'is_head_office': 1,
            'is_operational': 1,
            'contact_name': 'Ahmed Al Maktoum',
            'contact_email': 'ahmed@sdad.ae',
            'contact_position': 'Branch Manager',
            'address_line1': 'Al Muraqqabat Road',
            'city': 'Dubai',
            'district': 'Deira',
            'country': 'UAE',
            'phone': '+971-4-234-5678',
            'mobile': '+971-50-234-5678',
            'email': 'deira.hq@sdad.ae',
            'default_document_prefix': 'SDAD-HQ',
            'local_timezone': 'Asia/Dubai',
            'local_language': 'en',
            'is_active': 1,
            'status': 'active',
            'created_by': 1
        },
        {
            'entity_id': entity_ids.get('SDAD'),
            'branch_code': 'SDAD-RAK',
            'branch_name': 'SDAD Ras Al Khor Operations',
            'short_name': 'Ras Al Khor',
            'branch_type': 'warehouse_branch',
            'is_head_office': 0,
            'is_operational': 1,
            'contact_name': 'Hassan Ibrahim',
            'contact_email': 'hassan@sdad.ae',
            'contact_position': 'Operations Manager',
            'address_line1': 'Ras Al Khor Industrial Area',
            'city': 'Dubai',
            'district': 'Ras Al Khor',
            'country': 'UAE',
            'phone': '+971-4-345-6789',
            'mobile': '+971-50-345-6789',
            'email': 'rak.ops@sdad.ae',
            'default_document_prefix': 'SDAD-RAK',
            'local_timezone': 'Asia/Dubai',
            'is_active': 1,
            'status': 'active',
            'created_by': 1
        },
        {
            'entity_id': entity_ids.get('AFRA'),
            'branch_code': 'AFRA-JAF',
            'branch_name': 'AFRA JAFZA Main',
            'short_name': 'JAFZA',
            'branch_type': 'head_office',
            'is_head_office': 1,
            'is_operational': 1,
            'contact_name': 'Khalid Al Rashid',
            'contact_email': 'khalid@afra.ae',
            'contact_position': 'Branch Manager',
            'address_line1': 'Jebel Ali Free Zone',
            'address_line2': 'Warehouse Zone JAFZA North',
            'city': 'Dubai',
            'district': 'JAFZA',
            'country': 'UAE',
            'phone': '+971-4-345-6789',
            'mobile': '+971-50-345-6789',
            'email': 'jafza@afra.ae',
            'default_document_prefix': 'AFRA-JAF',
            'local_timezone': 'Asia/Dubai',
            'is_active': 1,
            'status': 'active',
            'created_by': 1
        },
        {
            'entity_id': entity_ids.get('CARM'),
            'branch_code': 'CARM-RETAIL',
            'branch_name': 'Carmania Retail Branch',
            'short_name': 'Retail',
            'branch_type': 'retail_branch',
            'is_head_office': 1,
            'is_operational': 1,
            'contact_name': 'Omar Al Nuaimi',
            'contact_email': 'omar@carmania.ae',
            'contact_position': 'Retail Manager',
            'address_line1': 'Khalifa City',
            'city': 'Abu Dhabi',
            'country': 'UAE',
            'phone': '+971-2-456-7890',
            'mobile': '+971-50-456-7890',
            'email': 'retail@carmania.ae',
            'default_document_prefix': 'CARM-RET',
            'local_timezone': 'Asia/Dubai',
            'is_active': 1,
            'status': 'active',
            'created_by': 1
        }
    ]

    branch_ids = {}
    for branch_data in branches:
        try:
            branch_id = create_branch(branch_data)
            branch_ids[branch_data['branch_code']] = branch_id
            print(f"  Created branch: {branch_data['branch_name']} (ID: {branch_id})")
        except Exception as e:
            print(f"  Branch may already exist: {e}")

    # Create Sites
    print("Creating sites...")

    sites = [
        {
            'entity_id': entity_ids.get('SDAD'),
            'branch_id': branch_ids.get('SDAD-RAK'),
            'site_code': 'SDAD-WH-RAS',
            'site_name': 'Ras Al Khor Main Warehouse',
            'short_name': 'RAK WH',
            'site_type': 'warehouse',
            'site_subtype': 'main_storage',
            'address_line1': 'Ras Al Khor Industrial Area 2',
            'city': 'Dubai',
            'district': 'Ras Al Khor',
            'country': 'UAE',
            'phone': '+971-4-345-6789',
            'email': 'warehouse.rak@sdad.ae',
            'contact_name': 'Hassan Ibrahim',
            'site_manager_name': 'Hassan Ibrahim',
            'site_manager_phone': '+971-50-345-6789',
            'site_manager_email': 'hassan@sdad.ae',
            'site_area_sqm': 5000,
            'covered_area_sqm': 4500,
            'yard_area_sqm': 500,
            'capacity_pallets': 2000,
            'capacity_items': 50000,
            'is_operational': 1,
            'is_active': 1,
            'status': 'active',
            'created_by': 1
        },
        {
            'entity_id': entity_ids.get('AFRA'),
            'branch_id': branch_ids.get('AFRA-JAF'),
            'site_code': 'AFRA-WH-JB03',
            'site_name': 'JAFZA Warehouse JB-03',
            'short_name': 'JB03',
            'site_type': 'warehouse',
            'site_subtype': 'bonded_storage',
            'address_line1': 'Jebel Ali Free Zone North',
            'address_line2': 'Warehouse JB-03',
            'city': 'Dubai',
            'district': 'JAFZA',
            'country': 'UAE',
            'phone': '+971-4-456-7890',
            'email': 'warehouse.jb03@afra.ae',
            'contact_name': 'Khalid Al Rashid',
            'site_manager_name': 'Mohammed Al Zaabi',
            'site_manager_phone': '+971-50-456-7890',
            'site_manager_email': 'm.zaabi@afra.ae',
            'site_area_sqm': 8000,
            'covered_area_sqm': 7500,
            'capacity_pallets': 3500,
            'capacity_items': 100000,
            'is_shared': 0,
            'is_operational': 1,
            'is_active': 1,
            'status': 'active',
            'created_by': 1
        },
        {
            'entity_id': entity_ids.get('SDAD'),
            'branch_id': branch_ids.get('SDAD-HQ'),
            'site_code': 'SDAD-OFF-DIR',
            'site_name': 'Deira Office',
            'short_name': 'Deira',
            'site_type': 'office',
            'address_line1': 'Al Muraqqabat Road',
            'city': 'Dubai',
            'district': 'Deira',
            'country': 'UAE',
            'phone': '+971-4-234-5678',
            'email': 'office@sdad.ae',
            'contact_name': 'Ahmed Al Maktoum',
            'site_area_sqm': 500,
            'covered_area_sqm': 500,
            'is_operational': 1,
            'is_active': 1,
            'status': 'active',
            'created_by': 1
        },
        {
            'entity_id': entity_ids.get('CARM'),
            'branch_id': branch_ids.get('CARM-RETAIL'),
            'site_code': 'CARM-SHOW',
            'site_name': 'Retail Showroom',
            'short_name': 'Showroom',
            'site_type': 'showroom',
            'address_line1': 'Khalifa City Mall Area',
            'city': 'Abu Dhabi',
            'country': 'UAE',
            'phone': '+971-2-456-7890',
            'email': 'showroom@carmania.ae',
            'contact_name': 'Omar Al Nuaimi',
            'site_area_sqm': 1000,
            'covered_area_sqm': 1000,
            'is_operational': 1,
            'is_active': 1,
            'status': 'active',
            'created_by': 1
        },
        {
            'entity_id': entity_ids.get('AFRA'),
            'branch_id': branch_ids.get('AFRA-JAF'),
            'site_code': 'AFRA-EXPORT',
            'site_name': 'Export Dispatch Area',
            'short_name': 'Export',
            'site_type': 'yard',
            'description': 'Container staging and export dispatch area',
            'address_line1': 'Jebel Ali Free Zone South',
            'city': 'Dubai',
            'district': 'JAFZA',
            'country': 'UAE',
            'site_area_sqm': 3000,
            'yard_area_sqm': 3000,
            'capacity_pallets': 500,
            'is_operational': 1,
            'is_active': 1,
            'status': 'active',
            'created_by': 1
        }
    ]

    for site_data in sites:
        try:
            site_id = create_site(site_data)
            print(f"  Created site: {site_data['site_name']} (ID: {site_id})")
        except Exception as e:
            print(f"  Site may already exist: {e}")

    # Create Relationships
    print("Creating relationships...")

    relationships = [
        {
            'source_entity_id': entity_ids.get('SDAD'),
            'target_entity_id': entity_ids.get('AFRA'),
            'relationship_type': 'sister',
            'relationship_subtype': 'group_company',
            'ownership_percentage': 0,
            'effective_date': '2018-01-01',
            'internal_pricing_policy': 'cost_plus',
            'trade_terms': 'Net 30',
            'credit_limit': 500000,
            'payment_terms': '30 days',
            'is_active': 1,
            'approval_required': 0,
            'notes': 'Group sister companies - internal transfers at cost',
            'created_by': 1
        },
        {
            'source_entity_id': entity_ids.get('SDAD'),
            'target_entity_id': entity_ids.get('CARM'),
            'relationship_type': 'associate',
            'relationship_subtype': 'joint_marketing',
            'ownership_percentage': 30,
            'effective_date': '2020-06-01',
            'internal_pricing_policy': 'standard',
            'trade_terms': 'Net 45',
            'credit_limit': 200000,
            'payment_terms': '45 days',
            'is_active': 1,
            'approval_required': 1,
            'notes': 'Associate company - shared marketing initiatives',
            'created_by': 1
        },
        {
            'source_entity_id': entity_ids.get('AFRA'),
            'target_entity_id': entity_ids.get('SDAD'),
            'relationship_type': 'supplier',
            'relationship_subtype': 'internal_supplier',
            'ownership_percentage': 0,
            'effective_date': '2018-01-01',
            'internal_pricing_policy': 'transfer_pricing',
            'trade_terms': 'Net 30',
            'credit_limit': 1000000,
            'payment_terms': '30 days',
            'is_active': 1,
            'approval_required': 0,
            'notes': 'AFRA supplies to SDAD - internal supply chain',
            'created_by': 1
        }
    ]

    for rel_data in relationships:
        try:
            rel_id = create_relationship(rel_data)
            print(f"  Created relationship: {rel_data['relationship_type']}")
        except Exception as e:
            print(f"  Relationship may already exist: {e}")

    # Create Intercompany Rules
    print("Creating intercompany rules...")

    rules = [
        {
            'rule_code': 'IC-SALES-SDAD-AFRA',
            'rule_name': 'Internal Sales SDAD to AFRA',
            'rule_type': 'transaction',
            'description': 'Transfer pricing for internal sales from SDAD to AFRA',
            'source_entity_id': entity_ids.get('SDAD'),
            'target_entity_id': entity_ids.get('AFRA'),
            'relationship_type': 'internal_sales',
            'pricing_policy': 'transfer_pricing',
            'markup_percentage': 5,
            'payment_terms': 'Net 30',
            'credit_limit': 500000,
            'is_auto_approve': 1,
            'is_active': 1,
            'priority': 1,
            'created_by': 1
        },
        {
            'rule_code': 'IC-TRANSFER-AFRA-SDAD',
            'rule_name': 'Stock Transfer AFRA to SDAD',
            'rule_type': 'transaction',
            'description': 'Inter-company stock transfer pricing',
            'source_entity_id': entity_ids.get('AFRA'),
            'target_entity_id': entity_ids.get('SDAD'),
            'relationship_type': 'internal_transfer',
            'pricing_policy': 'cost',
            'payment_terms': 'Net 30',
            'credit_limit': 1000000,
            'is_auto_approve': 1,
            'is_active': 1,
            'priority': 1,
            'created_by': 1
        }
    ]

    for rule_data in rules:
        try:
            rule_id = create_intercompany_rule(rule_data)
            print(f"  Created intercompany rule: {rule_data['rule_name']}")
        except Exception as e:
            print(f"  Intercompany rule may already exist: {e}")

    # Create Numbering Schemes
    print("Creating numbering schemes...")

    schemes = [
        {
            'entity_id': entity_ids.get('SDAD'),
            'document_type': 'invoice',
            'scheme_code': 'INV-SDAD',
            'scheme_name': 'SDAD Invoice Numbering',
            'prefix': 'INV-SDAD',
            'prefix_type': 'fixed',
            'include_year': 1,
            'include_month': 0,
            'include_day': 0,
            'year_format': 'YYYY',
            'sequence_length': 5,
            'sequence_format': 'zero_padded',
            'separator': '-',
            'reset_frequency': 'yearly',
            'is_active': 1,
            'notes': 'Invoice numbering for SDAD',
            'created_by': 1
        },
        {
            'entity_id': entity_ids.get('AFRA'),
            'document_type': 'invoice',
            'scheme_code': 'INV-AFRA',
            'scheme_name': 'AFRA Invoice Numbering',
            'prefix': 'INV-AFRA',
            'prefix_type': 'fixed',
            'include_year': 1,
            'include_month': 0,
            'include_day': 0,
            'year_format': 'YYYY',
            'sequence_length': 5,
            'sequence_format': 'zero_padded',
            'separator': '-',
            'reset_frequency': 'yearly',
            'is_active': 1,
            'notes': 'Invoice numbering for AFRA',
            'created_by': 1
        },
        {
            'entity_id': entity_ids.get('SDAD'),
            'document_type': 'purchase_order',
            'scheme_code': 'PO-SDAD',
            'scheme_name': 'SDAD Purchase Order Numbering',
            'prefix': 'PO-SDAD',
            'prefix_type': 'fixed',
            'include_year': 1,
            'sequence_length': 5,
            'sequence_format': 'zero_padded',
            'separator': '-',
            'reset_frequency': 'yearly',
            'is_active': 1,
            'created_by': 1
        }
    ]

    for scheme_data in schemes:
        try:
            scheme_id = create_numbering_scheme(scheme_data)
            print(f"  Created numbering scheme: {scheme_data['scheme_name']}")
        except Exception as e:
            print(f"  Numbering scheme may already exist: {e}")

    print("\n=== Multi-entity sample data seeded successfully! ===")
    print("\nSummary:")
    print(f"  Groups: 1 (MMD Group Holdings)")
    print(f"  Entities: 3 (SDAD, AFRA, Carmania)")
    print(f"  Branches: {len(branch_ids)}")
    print(f"  Sites: Multiple (warehouses, offices, showrooms)")
    print(f"  Relationships: Intercompany links created")
    print(f"  Numbering Schemes: Created for SDAD and AFRA")


if __name__ == '__main__':
    seed_multi_entity_data()
