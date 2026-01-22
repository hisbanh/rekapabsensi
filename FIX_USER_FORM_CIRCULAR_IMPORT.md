# Fix: User Edit Form TypeError - Circular Import Issue

## Problem
When accessing the user edit page at `/manage/users/{id}/edit/`, the application threw a TypeError:
```
TypeError: 'NoneType' object is not callable
```

The error occurred at line 1492 in `attendance/views.py`:
```python
form = UserForm(instance=user_obj)
```

## Root Cause
The issue was caused by a circular import problem in the forms module structure:

1. **Two forms modules exist:**
   - `attendance/forms.py` (legacy file containing UserForm and other forms)
   - `attendance/forms/` (new package directory with teacher forms)

2. **Circular import:**
   - `attendance/views.py` imports from `attendance.forms`
   - Python resolves this to `attendance/forms/__init__.py` (the package)
   - The package's `__init__.py` tried to import from `attendance.forms` (creating a circular reference)
   - This caused `UserForm` to be `None` instead of the actual form class

## Solution
Modified `attendance/forms/__init__.py` to load the legacy forms from `forms.py` using a different module name to avoid the circular import:

1. **Temporarily remove the package from sys.modules**
2. **Load forms.py as a separate module** (`attendance.legacy_forms`)
3. **Extract the form classes** from the loaded module
4. **Restore the package module** to sys.modules

This approach allows both the forms package and the legacy forms.py file to coexist without circular import issues.

## Files Modified
- `attendance/forms/__init__.py` - Updated import strategy to avoid circular imports

## Testing
Verified the fix with:
1. ✓ Django system check passes
2. ✓ UserForm can be imported successfully
3. ✓ UserForm can be instantiated (empty form)
4. ✓ UserForm can be instantiated with user instance
5. ✓ User edit view returns 200 status code
6. ✓ Development server runs without errors

## Status
**FIXED** - The user edit page now loads correctly without TypeError.

## Next Steps (Optional)
For better long-term maintainability, consider:
1. Migrating all legacy forms from `forms.py` into the `forms/` package as separate files
2. Or renaming the forms package to avoid naming conflicts (e.g., `form_classes/`)
3. Updating all imports throughout the codebase to use the new structure

However, the current solution is stable and works correctly.
