# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django 4.2+ training manager (originally for swim training). Domain: an `Agenda` schedules `Event`s, each made up of ordered `Round`s, each containing `Exercise`s with a `Stroke` and `EnergySegment`/`EnergySystem`. `Member`s are attached to agendas/events for attendance. Auth uses a custom user model (`customuser.CustomUser`) with `language` + `is_foo_admin` fields and django-hijack for impersonation.

## Common commands

The Django project package is literally named `django-trainingmanager` (with a hyphen). The settings module is `'django-trainingmanager.settings'` — referenced as a string by `manage.py`. **Do not** rename or `import` it as a Python module; only `manage.py` and `wsgi.py` reach it.

```bash
python manage.py runserver
python manage.py migrate
python manage.py makemigrations <app>
python manage.py loaddata db.json          # seed/restore from checked-in fixture
python manage.py createsuperuser
python manage.py collectstatic
python manage.py test                      # run all tests
python manage.py test agenda.tests         # run a single app's tests
python manage.py test agenda.tests.SomeTestCase.test_method
django-admin makemessages -l fr -l nl      # extract translations (locale/ has fr, nl)
django-admin compilemessages
```

Migrations are not currently checked in (see `git status`); the first migrate after clone will create them, or `loaddata db.json` after migrating reseeds the bundled SQLite fixture.

## Architecture: generic CRUD scaffolding

The non-obvious heart of this codebase is a convention-based scaffold in `tools/` that wires up CRUD views and URLs automatically. Understanding it is required to make sense of why each app's `urls.py` is two lines.

### `tools/generic_class.py:GenericClass`
Abstract model base. In `__init__` it derives URL-name strings from `_meta.app_label` / `_meta.model_name` (`<app>:<model>_change`, `_add`, `_detail`, `_delete`, `_list`) and exposes `get_change_url()`, `get_add_url()`, `get_detail_url()`, `get_delete_url()`, `get_list_url()`, `get_full_url()` (prefixes `settings.WEBSITE`). Templates rely on these methods being present — every domain model inherits from `GenericClass`.

### `tools/generic_views.py`
`GenericCreateView`, `GenericListView`, `GenericUpdateView`, `GenericDetailView`, `GenericDeleteView`. Each derives `app_name` / `model_name` / `success_url` from `self.model._meta` in `__init__`. Default templates: `update.html`, `list.html`, `detail.html` (in `templates/`). App views typically subclass these and only set `model = X`.

### `tools/generic_urls.py:add_url_from_generic_views(app_views_module)`
Introspects the named views module and auto-registers URL patterns **by class-name suffix**:

| Class suffix  | Path                       | URL name           |
|---------------|----------------------------|--------------------|
| `CreateView`  | `<model>/add/`             | `<model>_add`      |
| `ListView`    | `<model>/`                 | `<model>_list`     |
| `UpdateView`  | `<model>/<int:pk>/change/` | `<model>_change`   |
| `DetailView`  | `<model>/<int:pk>/`        | `<model>_detail`   |
| `DeleteView`  | `<model>/<int:pk>/delete`  | `<model>_delete`   |

So an app's `urls.py` is just:
```python
app_name = 'agenda'
urlpatterns = add_url_from_generic_views('agenda.views')
urlpatterns.append(path(...))   # extra non-CRUD routes
```
**Implication**: to add a new model, define `<Model>{Create,List,Update,Detail,Delete}View` classes in `<app>/views.py` with `model = <Model>` — URLs and reverse names are wired automatically. Don't invent a different naming convention; the introspection relies on the suffix exactly.

### `tools/buildclass.py`
Standalone code generator (run as `python tools/buildclass.py`) that prints starter `views.py` / `urls.py` / `models.py` for a new `(app, label, ClassName)`. Output references `view_breadcrumbs`, which is **not** in `requirements.txt` — treat it as boilerplate to copy and edit, not a complete recipe.

## Modal forms convention

CRUD that opens in a Bootstrap modal uses `bootstrap_modal_forms.generic.BSModal{Create,Update,Delete}View` with `template_name = 'modal.html'` (or `'modal_round.html'` for nested formsets) — see `agenda/views.py`, `round/views.py`. Plain (non-modal) CRUD uses the `Generic*View` base classes. Both styles coexist in the same app; pick by whether the UX wants a modal.

`round/views.py` additionally manages a nested `RoundExerciseFormSet` inside `form_valid` under `transaction.atomic()` — that's the pattern for any "object with inline children" form here.

## URL namespacing

Root URLs (`django-trainingmanager/urls.py`) include each app under its own namespace: `agenda:`, `event:`, `member:`, `round:`, `exercise:`. `GenericClass.get_*_url()` methods build names like `agenda:agenda_change` — keep `app_name` set in each app's `urls.py` or reverse lookups break.

## Templates

Generic CRUD templates live in the project-level `templates/` dir (`list.html`, `update.html`, `detail.html`, `delete.html`, `modal.html`, `modal_round.html`, `base.html`, `_header.html`, `_footer.html`, `index.html`). Per-model overrides go in app templates (e.g. `AgendaDetailView.template_name = 'agenda.html'`). The `common_tags` template library (root `common_tags.py`) provides `hash`, `verbose_name`, `app_name` filters and is registered in `TEMPLATES.OPTIONS.libraries`.

## i18n

`gettext`/`gettext_lazy` is used throughout models, forms, and views. Languages: `en`, `fr`, `nl`. `set_lang` view in root `urls.py` switches via `?lang=` and persists in cookie. When adding user-visible strings, wrap with `_(...)` and run `makemessages`.

## Known issues / gotchas

- `agenda/views.py:create_events` uses `request.is_ajax()`, which was **removed in Django 3.1**. Under Django 4.2 (per `requirements.txt`) this raises `AttributeError`. If you touch this view, replace with `request.headers.get('x-requested-with') == 'XMLHttpRequest'`.
- `settings.py` has `DEBUG = True`, a hardcoded `SECRET_KEY`, and `ALLOWED_HOSTS = ['*']` checked into the repo. Treat it as dev-only; production deploys need a `local_settings.py` (already in `.gitignore`).
- `WKHTMLTOPDF_CMD = 'xvfb-run /usr/bin/wkhtmltopdf'` is Linux-specific. On Windows dev, override in local settings or expect PDF views to fail.
- `requirements.txt` pins `selenium==3.14.0` and `pytz==2018.5` — quite old; do not assume modern Selenium 4 APIs.
- `STATIC_ROOT` and `STATICFILES_DIRS` both point at `static/` via mutually exclusive comment toggles in `settings.py` (lines 117–120). Switching between dev and prod requires uncommenting the right one — there is no `DEBUG`-aware branch.
- The default SQLite DB is checked in (`db.sqlite3`) along with a JSON fixture (`db.json`). Migrations directories are currently untracked; run `makemigrations` before `migrate` on a fresh clone if needed.
