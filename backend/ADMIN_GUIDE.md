# Nativo Admin Interface Guide

## Overview

The Nativo admin interface is powered by [Starlette Admin](https://github.com/jowilf/starlette-admin) and provides a comprehensive web-based interface for managing all aspects of the Nativo platform.

## Accessing the Admin Interface

1. **URL**: `http://localhost:8000/admin` (when running locally)
2. **Authentication**: Only users with admin role or superuser status can access the admin interface

## Login Credentials

- Username: Your Nativo username or email
- Password: Your Nativo password

**Important**: Only accounts with:
- `is_superuser = True`, OR
- `role = UserRole.ADMIN`

will be granted access to the admin interface.

## Available Models

The admin interface provides full CRUD (Create, Read, Update, Delete) operations for the following models:

### Core Models
- **Users**: Manage user accounts, roles, and permissions
- **Languages**: Manage endangered languages in the system
- **Words**: Manage word entries with linguistic information
- **Documents**: Manage text content (definitions, stories, etc.)

### Media Models
- **Audio**: Manage audio recordings
- **Images**: Manage image references
- **Locations**: Manage geographic locations for dialectal tracking

### Organization Models
- **Tags**: Manage categorization tags for words
- **User Languages**: Manage user-language relationships and permissions

## Features

### Search and Filter
- Most models support full-text search across relevant fields
- Use the search bar at the top of each model list view

### Sorting
- Click on column headers to sort by that field
- Supports ascending and descending order

### Pagination
- Default: 25 items per page
- Options: 25, 50, or 100 items per page
- Use pagination controls at the bottom of each list

### Bulk Actions
- Select multiple items using checkboxes
- Apply bulk delete operations (use with caution!)

### Data Export
- Export data in various formats (CSV, Excel, etc.)
- Available from the list view of each model

## Security Features

1. **Authentication Required**: All admin routes require valid authentication
2. **Role-Based Access**: Only admin and superuser roles are permitted
3. **Session Management**: Sessions expire after 4 hours of inactivity
4. **Password Protection**: Passwords are never displayed in the admin interface

## Best Practices

1. **Create a Dedicated Admin Account**: Don't use regular user accounts for admin tasks
2. **Regular Backups**: Always backup the database before making bulk changes
3. **Test Changes**: Use the detail view to verify changes before saving
4. **Audit Trail**: All models track creation and update timestamps

## Development Notes

### Adding New Models to Admin

To add a new model to the admin interface:

1. Create a ModelView class in `app/admin.py`:
```python
class MyModelAdmin(ModelView):
    exclude_fields_from_create = ["created_at", "updated_at"]
    exclude_fields_from_edit = ["created_at", "updated_at"]
    searchable_fields = ["field1", "field2"]
    sortable_fields = ["field1", "created_at"]
    page_size = 25
```

2. Register the view in `create_admin()`:
```python
admin.add_view(MyModelAdmin(MyModel, icon="fa fa-icon-name"))
```

### Customizing the Admin Interface

- **Change Theme**: Modify the Admin instance configuration
- **Add Custom Views**: Create custom view classes extending `BaseAdmin`
- **Add Custom Actions**: Define custom row and batch actions in ModelView classes

## Troubleshooting

### Cannot Login
- Verify your user has admin role or is_superuser enabled
- Check that the user account is active (is_active=True)
- Ensure the password is correct

### Missing Data
- Check filters and search criteria
- Verify pagination settings
- Ensure data exists in the database

### Performance Issues
- Reduce page_size for large datasets
- Add database indexes for frequently searched fields
- Consider implementing custom queries for complex views

## Technical Details

- **Framework**: Starlette Admin 0.15.1+
- **Database**: SQLAlchemy ORM
- **Session Backend**: Secure cookie-based sessions
- **Session Lifetime**: 4 hours
- **Icons**: FontAwesome 4.7

## Support

For issues or questions about the admin interface:
1. Check the [Starlette Admin documentation](https://jowilf.github.io/starlette-admin/)
2. Review the `app/admin.py` file for implementation details
3. Check server logs for authentication or access errors

