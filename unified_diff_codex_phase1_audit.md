```diff
diff --git a/core_ui_service/lifecycle/__init__.py b/core_ui_service/lifecycle/__init__.py
index 4ebfcfc..1b2eccc 100644
--- a/core_ui_service/lifecycle/__init__.py
+++ b/core_ui_service/lifecycle/__init__.py
@@ -1,3 +1,3 @@
-from core_ui_service.lifecycle.routes import router
+from .routes import router
 
 __all__ = ["router"]
diff --git a/core_ui_service/lifecycle/routes.py b/core_ui_service/lifecycle/routes.py
index ef1fc65..2749186 100644
--- a/core_ui_service/lifecycle/routes.py
+++ b/core_ui_service/lifecycle/routes.py
@@ -12,14 +12,14 @@ from datetime import datetime, timezone
 
 from fastapi import APIRouter, HTTPException
 
-from core_ui_service.lifecycle.models import (
+from .models import (
     BuildResponse,
     DCFRequest,
     DCFResponse,
     ReleaseResponse,
     StateResponse,
 )
-from core_ui_service.lifecycle.runner import compile_dcf_worksheet, run_dcf
+from .runner import compile_dcf_worksheet, run_dcf
 
 from fin123.worksheet.compiled import CompiledWorksheet
 
diff --git a/core_ui_service/lifecycle/runner.py b/core_ui_service/lifecycle/runner.py
index 3730bec..eb787b7 100644
--- a/core_ui_service/lifecycle/runner.py
+++ b/core_ui_service/lifecycle/runner.py
@@ -8,7 +8,7 @@ from fin123.worksheet import compile_worksheet, from_json_records, parse_workshe
 from fin123.worksheet.compiled import CompiledWorksheet
 from fin123.worksheet.types import ColumnSchema, ColumnType
 
-from core_ui_service.lifecycle.models import DCFRequest, DCFResponse, YearRow
+from .models import DCFRequest, DCFResponse, YearRow
 
 PROJECTION_YEARS = 5
 
diff --git a/core_ui_service/main.py b/core_ui_service/main.py
index 0c74bd0..25078ed 100644
--- a/core_ui_service/main.py
+++ b/core_ui_service/main.py
@@ -26,7 +26,10 @@ from fastapi import FastAPI, Request
 from fastapi.responses import JSONResponse
 from fin123.ui.server import create_app as create_core_ui_app
 
-from core_ui_service.lifecycle import router as lifecycle_router
+try:
+    from core_ui_service.lifecycle import router as lifecycle_router
+except ModuleNotFoundError:
+    from lifecycle import router as lifecycle_router
 
 PROJECT_DIR = Path(
     os.environ.get(
diff --git a/render.yaml b/render.yaml
index bb049dd..9a225b2 100644
--- a/render.yaml
+++ b/render.yaml
@@ -4,12 +4,10 @@ services:
     runtime: python
     rootDir: core_ui_service
     buildCommand: pip install -r requirements.txt
-    startCommand: uvicorn core_ui_service.main:app --host 0.0.0.0 --port $PORT --workers 2
+    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
     healthCheckPath: /healthz
     envVars:
       - key: PYTHON_VERSION
         value: "3.12"
       - key: FIN123_PROJECT_DIR
-        value: /opt/render/project/src/core_ui_service/seed/dcf_demo
-      - key: PYTHONPATH
-        value: /opt/render/project/src
+        value: /opt/render/project/src/seed/dcf_demo
```
