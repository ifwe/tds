#!/bin/bash

echo "// tds/web/js/home.js" > tds/web/js/app.js
cat tds/web/js/home.js >> tds/web/js/app.js
echo "// tds/web/js/login.js" >> tds/web/js/app.js
cat tds/web/js/login.js >> tds/web/js/app.js
echo "// tds/web/js/index.js" >> tds/web/js/app.js
cat tds/web/js/index.js >> tds/web/js/app.js
