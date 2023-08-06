<?php
require_once('config.php');
set_include_path(get_include_path() . PATH_SEPARATOR . ADODB_PATH);
require_once('adodb.inc.php');
require_once('adodb-exceptions.inc.php');
class DataPoint
{
	public $date;
	public $value;
}
/*
* Enable ADOdb
*/
$db = newAdoConnection('mysqli');
$ADODB_FETCH_MODE = ADODB_FETCH_NUM;
$db->connect(SQL_HOST, SQL_USER, SQL_PASS, SQL_DB);	
$dayIndx =(date("Y")*10000+date("n")*100+(date("j")));
$len=4;
if(isset($_GET['len']) && is_numeric($_GET['len']))
{
	$len = intval($_GET['len']);
	
}
$query ='SELECT  EventTimeStamp, Value, Name,  	IsWorking FROM `DataPoints` left join Devices on DataPoints.DeviceID= Devices.ID  WHERE DayIndx >=' .$dayIndx.' and EventTimeStamp >= date_add(now(), INTERVAL  -'.$len.' HOUR) order by DeviceID desc , EventTimeStamp asc  LIMIT 0, 1000';
		//$this->DB->debug=true;
$rs = $db->Execute($query);
$results =array();
$label = "";
$workFlags = array();
$oldLabel='';
$stopStoreFlags=false;
while ($rs && !$rs->EOF)
{
	
	$label=$rs->fields[2];
	if($oldLabel!='' && $oldLabel!=$label)
		$stopStoreFlags=true;
	if($oldLabel!=$label)
		$oldLabel=$label;
	if(!isset($results[$label]))
		$results[$label]= array();
	$pt = new DataPoint();
	$pt->date= $rs->fields[0];
	$pt->value= $rs->fields[1];
	array_push($results[$label], $pt);
	
	$pt = new DataPoint();
	$pt->date= $rs->fields[0];
	$pt->value= $rs->fields[3];
	if(!$stopStoreFlags)
		array_push($workFlags, $pt);
	$rs->MoveNext();
}
$results['work']=$workFlags;
$rawData = json_encode($results);
header('Content-Type: application/json');
echo $rawData;

?>