<?php
/** logout.php */
session_destroy();
header('Location: /');
exit;
