{
    "name": "Tally Bridge",
    "version": "19.0.1.0.0",
    "summary": "Odoo 19 to TallyPrime integration bridge",
    "description": """
Agent-driven Odoo 19 ↔ TallyPrime integration.
Compatible with Odoo 19 Community and Enterprise editions.
""",
    "author": "Your Company",
    "license": "LGPL-3",
    "depends": ["base", "account"],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "data/ir_cron_data.xml",
        "views/tally_config_views.xml",
        "views/tally_mapping_views.xml",
        "views/tally_sync_queue_views.xml",
        "views/tally_menus.xml",
    ],
    "installable": True,
    "application": True,
}
