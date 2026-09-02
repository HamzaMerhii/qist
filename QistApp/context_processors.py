def nav_placeholders(request):
    """Sidebar entries for BRD-scoped modules that don't exist as apps yet.
    Remove an item here once its app/urls are built for real.
    """
    return {
        "not_built_nav": [
            ("Invoices", "description"),
            ("Returns", "assignment_return"),
            ("Ledger", "account_balance"),
            ("Notifications", "notifications"),
            ("Audit Logs", "history"),
            ("Settings", "settings"),
        ]
    }
