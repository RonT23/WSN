<?php
	$n_historical_data = 1; // telemetry recording to capture for every sensor 

	$date = date("Y/m/d");  // current date : YYYY/MM/DD
	$time = date("H:i:s");  // current time : hh:mm:ss

	$st         = $_GET['st'];   // station id
	$temp       = $_GET['t'];    // internal temperature
	$bus_vol    = $_GET['v'];    // bus voltage
	$bus_cur    = $_GET['i'];    // bus current
	$solar_vol  = $_GET['sv'];   // solar panel voltage
	$heart_beat = $_GET['hb'];   // hartbeat
	$op_mode    = $_GET['m'];    // operation mode

	$telemetry =  $date.","
				.$time.","
				.$temp.","
				.$bus_vol.","
				.$bus_cur.","
				.$solar_vol.","
				.$heart_beat.","
				.$op_mode."\n";

// write telemetry on the file
    $filePath = "./telemetry_files/telemetry_".$st;
    $lines = count(file($filePath));

    if($lines < $n_historical_data){	
		$fp1 = fopen($filePath, 'a');
		fwrite($fp1,$telemetry);
		fclose($fp1);
		echo 1;
	}else{	
		$fp1 = fopen($filePath, 'w');
		fwrite($fp1,$telemetry);
		fclose($fp1);
		echo 0;
	}
?>
