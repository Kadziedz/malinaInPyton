<?php
	function myDebug($message)
	{
		error_log("KaDe DEBUG: ".print_r($message, true));		
	}
	class Request
	{
		public $id	=1;
		public $lowerTempSensor	;
		public $higherTempSensor	;
		public $minimumTempDiff;
		public $dayStart;
		public $dayStop	;
		public $decisionDelay;
		public $measurementSamplesCount	;
		public $maxStateTime	;
		public $controlInterval	;
		public $dataSaveInterval;
		public $AmbientTempSensor;
		public $MinimumAmbientTemp;
		public $IsAuto;
		public $lowerTempSensorOffset	;
		public $higherTempSensorOffset	;
		public $ambientTempSensorOffset;
	}	

require_once('RestHelper.php');
	$worker = new RestHelper();
	$req= new Request();
	$req->id	= 1;
	$req->LowerTempSensor	=$_POST['LowerTempSensor'];
	$req->HigherTempSensor	=$_POST['HigherTempSensor'];
	$req->AmbientTempSensor	=$_POST['AmbientTempSensor'];
	$req->MinimumTempDiff =intval($_POST['MinimumTempDiff']);
	$req->MinimumAmbientTemp =intval($_POST['MinimumAmbientTemp']);
	$req->IsAuto= $_POST['IsAuto']=='true';
	$req->DayStart =intval($_POST['DayStart']);
	$req->DayStop	=intval($_POST['DayStop']);
	$req->DecisionDelay=intval($_POST['DecisionDelay']);
	$req->MeasurementSamplesCount	=intval($_POST['MeasurementSamplesCount']);
	$req->MaxStateTime	=intval($_POST['MaxStateTime']);
	$req->ControlInterval	=intval($_POST['ControlInterval']);
	$req->DataSaveInterval=intval($_POST['DataSaveInterval']);
	$req->LowerTempSensorOffset=floatval($_POST['LowerTempSensorOffset']);
	$req->HigherTempSensorOffset=floatval($_POST['HigherTempSensorOffset']);
	$req->AmbientTempSensorOffset=floatval($_POST['AmbientTempSensorOffset']);
//myDebug(json_encode($req));	
header('Content-Type: application/json');
$result = $worker->CallAPI("POST",'api/cfg', $req);

echo $result;
	//myDebug($result);

?>
