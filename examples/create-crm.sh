#!/bin/bash
# Example: Build a simple CRM from scratch using fibery CLI
# This creates a Space, 3 databases, fields, relations, and sample data.

set -euo pipefail
WS="myworkspace"  # Change to your workspace alias

echo "=== Creating CRM Space ==="
fibery $WS space create "My CRM" --color "#3E53B4"

echo "=== Creating Databases ==="
fibery $WS schema create-type --space "My CRM" --name "Accounts" --color "#3E53B4" \
  --with-mixins "fibery/rank-mixin,comments/comments-mixin"
fibery $WS schema create-type --space "My CRM" --name "Contacts" --color "#8EC351" \
  --with-mixins "fibery/rank-mixin,comments/comments-mixin"
fibery $WS schema create-type --space "My CRM" --name "Interactions" --color "#FBA32F" \
  --with-mixins "fibery/rank-mixin,comments/comments-mixin"

echo "=== Adding Fields to Accounts ==="
fibery $WS schema create-field --type "My CRM/Accounts" --name "My CRM/Website" --field-type fibery/text --ui-type url
fibery $WS schema create-field --type "My CRM/Accounts" --name "My CRM/Revenue" --field-type fibery/decimal --money
fibery $WS schema create-field --type "My CRM/Accounts" --name "My CRM/Employees" --field-type fibery/int
fibery $WS schema create-field --type "My CRM/Accounts" --name "My CRM/Active" --field-type fibery/bool
fibery $WS schema create-rich-text --type "My CRM/Accounts" --name "My CRM/Notes"
fibery $WS schema create-files --type "My CRM/Accounts" --name "My CRM/Documents"
fibery $WS schema create-enum --type "My CRM/Accounts" --name "My CRM/Tier" --options "Enterprise,Mid-Market,SMB,Startup"

echo "=== Adding Fields to Contacts ==="
fibery $WS schema create-field --type "My CRM/Contacts" --name "My CRM/Email" --field-type fibery/text --ui-type email
fibery $WS schema create-field --type "My CRM/Contacts" --name "My CRM/Phone" --field-type fibery/text --ui-type phone
fibery $WS schema create-field --type "My CRM/Contacts" --name "My CRM/Title" --field-type fibery/text
fibery $WS schema create-enum --type "My CRM/Contacts" --name "My CRM/Status" --options "Lead,Active,Churned,VIP"

echo "=== Adding Fields to Interactions ==="
fibery $WS schema create-field --type "My CRM/Interactions" --name "My CRM/Date" --field-type fibery/date-time
fibery $WS schema create-field --type "My CRM/Interactions" --name "My CRM/Duration" --field-type fibery/int
fibery $WS schema create-rich-text --type "My CRM/Interactions" --name "My CRM/Summary"
fibery $WS schema create-enum --type "My CRM/Interactions" --name "My CRM/Type" --options "Call,Email,Meeting,Demo"
fibery $WS schema create-workflow --type "My CRM/Interactions" \
  --states "Scheduled:todo|Confirmed:todo|In Progress:started|Completed:done|Cancelled:finished"

echo "=== Creating Relations ==="
fibery $WS schema create-relation --from-type "My CRM/Contacts" --to-type "My CRM/Accounts" \
  --name-forward "My CRM/Account" --name-back "My CRM/Contacts" --cardinality one-to-many
fibery $WS schema create-relation --from-type "My CRM/Interactions" --to-type "My CRM/Contacts" \
  --name-forward "My CRM/Attendees" --name-back "My CRM/Interactions" --cardinality many-to-many
fibery $WS schema create-relation --from-type "My CRM/Interactions" --to-type "My CRM/Accounts" \
  --name-forward "My CRM/Account" --name-back "My CRM/Interactions" --cardinality one-to-many

echo "=== Creating Sample Data ==="
fibery $WS create "My CRM/Accounts" --fields '{"My CRM/name":"Acme Corp","My CRM/Website":"acme.com","My CRM/Revenue":5200000,"My CRM/Employees":150,"My CRM/Active":true}'
fibery $WS create "My CRM/Contacts" --fields '{"My CRM/name":"Sarah Chen","My CRM/Email":"sarah@acme.com","My CRM/Title":"VP Engineering"}'

echo "=== Done! Open Fibery to see your new CRM. ==="
