<?php
require_once('RestHelper.php');
$worker = new RestHelper();
header('Content-Type: application/json');
$result = $worker->CallAPI("GET",'api');
echo $result;
?>
