app_name = "asset_customization"
app_title = "Asset Customization"
app_publisher = "Reformiqo"
app_description = "Asset Component Replacement workflow for ERPNext"
app_email = "consultant.reformiqo@gmail.com"
app_license = "MIT"
required_apps = ["frappe", "erpnext"]

# C-01: Inject "Replace Component" button on Asset form
doctype_js = {
    "Asset": "public/js/asset.js",
}

# Custom fields on Asset
after_install = "asset_customization.setup.after_install"
after_migrate = "asset_customization.setup.after_migrate"
