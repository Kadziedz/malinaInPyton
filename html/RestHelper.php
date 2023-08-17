<?php
require_once('config.php');
class RestHelper
{
	private const URL = WEBAPI_URL;
	public function CallAPI($method, $cmd, $data = false)
	{
		$curl = curl_init();
		$url = RestHelper::URL.$cmd;
		switch ($method)
		{
			case "POST":
				curl_setopt($curl, CURLOPT_POST, 1);

				if ($data)
				{
					$headers = [
									"Content-Type: application/json",
									"X-Content-Type-Options:nosniff",
									"Accept:application/json",
									"Cache-Control:no-cache"
								];
					curl_setopt($curl,CURLOPT_RETURNTRANSFER, true);
					curl_setopt($curl,CURLOPT_POSTFIELDS, json_encode($data)); 
					curl_setopt($curl,CURLOPT_HTTPHEADER, $headers);
				}
				break;
			case "PUT":
				curl_setopt($curl, CURLOPT_PUT, 1);
				break;
			default:
				if ($data)
					$url = sprintf("%s?%s", $url, http_build_query($data));
		}

		// Optional Authentication:
		//curl_setopt($curl, CURLOPT_HTTPAUTH, CURLAUTH_BASIC);
		//curl_setopt($curl, CURLOPT_USERPWD, "username:password");
		curl_setopt($curl, CURLOPT_URL, $url);
		curl_setopt($curl, CURLOPT_RETURNTRANSFER, 1);
		$result = curl_exec($curl);
		curl_close($curl);
		return $result;
	}
}
?>
