#!/bin/bash

# Create base templates directory if it doesn't exist
mkdir -p templates/includes
mkdir -p templates/accounts
mkdir -p templates/projects/tabs
mkdir -p templates/content_templates
mkdir -p templates/core

# Create includes templates
touch templates/includes/sidebar.html
touch templates/includes/header.html
touch templates/includes/footer.html
touch templates/includes/messages.html

# Create accounts templates
touch templates/accounts/login.html
touch templates/accounts/signup.html
touch templates/accounts/dashboard.html
touch templates/accounts/profile.html

# Create projects templates
touch templates/projects/project_list.html
touch templates/projects/project_form.html
touch templates/projects/project_confirm_delete.html
touch templates/projects/project_detail.html
touch templates/projects/tabs/upload_tab.html
touch templates/projects/tabs/prompts_tab.html
touch templates/projects/tabs/generate_tab.html

# Create content_templates templates
touch templates/content_templates/template_list.html
touch templates/content_templates/template_form.html
touch templates/content_templates/template_confirm_delete.html
touch templates/content_templates/template_detail.html

# Create core templates
touch templates/core/home.html
touch templates/core/pricing.html
