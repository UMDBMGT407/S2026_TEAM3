# Revert: login “denied access” notice

This folder includes **`login_denied_notice.forward.patch`**, which is the unified diff that added:

- `next_url_allowed_for_role`, extended `redirect_to_login_with_next`, `auth_login` / `require_roles` / `admin_page` updates in [`app.py`](../app.py)
- `login_denied` alert in [`Templates/Admin/index.html`](../Templates/Admin/index.html)

## Undo the feature

From the **repository root** (`S2026_TEAM3`):

```sh
patch -R -p1 < patches/login_denied_notice.forward.patch
```

- **`-p1`** strips the first path segment (`a/` and `b/`) so files match `app.py` and `Templates/Admin/index.html`.

If `patch` fails (line endings, local edits, or index hash mismatch), restore the two files from Git instead:

```sh
git checkout -- app.py Templates/Admin/index.html
```

(Only use that if you have not committed other changes you need in those files.)
