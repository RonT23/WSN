<?php
	$date = date("Y/m/d");  // current date : YYYY/MM/DD
	$time = date("H:i:s");  // current time : hh:mm:ss

	$st    = $_GET['st'];   // station id
	$hum   = $_GET['h'];    // humidity
	$temp  = $_GET['t'];    // temperature
	$pres  = $_GET['p'];    // pressure
	$dir   = $_GET['d'];    // wind direction
	$rain  = $_GET['r'];    // rain amount 
	$speed = $_GET['v'];    // wind speed 

	$input_data = $st.","
				 .$date.","
				 .$time.","
				 .$hum.","
				 .$temp.","
				 .$pres.","
				 .$dir.","
				 .$rain.","
				 .$speed."\n";

//store into the backup file
	$filePath = "./backup/backup_file";
	$fp1 = fopen($filePath, 'a');
	fwrite($fp1,$input_data);
	fclose($fp1);

	$con = include 'connect.php';
	if (mysqli_connect_errno()) { exit(); } 
	
//upload data 
	$sql = "INSERT INTO `weather_data` (`Station_ID`,`Date`,`Time`,`Humidity`,`Temperature`,`Pressure`,`Wind_Direction`,`Wind_Speed`,`Rainfall`) VALUES ('$st','$date','$time', '$hum','$temp','$pres','$dir','$speed', '$rain');";
	$con->query($sql);
	$con->close();

echo 200;
?>
