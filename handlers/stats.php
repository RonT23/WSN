<?php
	$con = include 'connect.php';
	if (mysqli_connect_errno()) { exit(); } 
	
	$day   = date('d');
	$month = date('m');
	$year  = date('Y');
	
	$st = $_GET['st'];
	
// get the minimum values
	$sql = "SELECT min(Temperature) as `min_temp`, min(Humidity) as `min_hum`, min(Pressure) as `min_pres`, min(Wind_Speed) as `min_wind`, min(Rainfall) as `min_rain` from `weather_data` WHERE Station_ID = '$st' and day(`Date`) = $day and month(`Date`) = $month and year(`Date`) = $year;";

	$result = $con->query($sql);
	while($row = $result->fetch_assoc()) {
		$min_temp  = $row["min_temp"];
		$min_hum   = $row["min_hum"];
		$min_pres  = $row["min_pres"];
		$min_wind  = $row["min_wind"];
		$min_rain  = $row["min_rain"];
 	 }	
	
	$min_output = $min_temp.",".
				  $min_hum.",".
				  $min_pres.",".
				  $min_wind.",".
				  $min_rain."\n";
	
	mysqli_free_result($result);

// get the maximum values
	$sql = "SELECT max(Temperature) as `max_temp`, max(Humidity) as `max_hum`, max(Pressure) as `max_pres`, max(Wind_Speed) as `max_wind`, max(Rainfall) as `max_rain` from `weather_data` WHERE Station_ID = '$st' and day(`Date`) = $day and month(`Date`) = $month and year(`Date`) = $year;";

	$result = $con->query($sql);
	while($row = $result->fetch_assoc()) {
		$max_temp  = $row["max_temp"];
		$max_hum   = $row["max_hum"];
		$max_pres  = $row["max_pres"];
		$max_wind  = $row["max_wind"];
		$max_rain  = $row["max_rain"];
 	 }	
	
	$max_output = $max_temp.",".
				  $max_hum.",".
				  $max_pres.",".
				  $max_wind.",".
				  $max_rain."\n";
	
	mysqli_free_result($result);

// get the average values
	$sql = "SELECT avg(Temperature) as `avg_temp`, avg(Humidity) as `avg_hum`, avg(Pressure) as `avg_pres`, avg(Wind_Speed) as `avg_wind`, avg(Rainfall) as `avg_rain` from `weather_data` WHERE Station_ID = '$st' and day(`Date`) = $day and month(`Date`) = $month and year(`Date`) = $year;";

	$result = $con->query($sql);
	while($row = $result->fetch_assoc()) {
		$avg_temp  = $row["avg_temp"];
		$avg_hum   = $row["avg_hum"];
		$avg_pres  = $row["avg_pres"];
		$avg_wind  = $row["avg_wind"];
		$avg_rain  = $row["avg_rain"];
 	 }	
	
	$avg_output = $avg_temp.",".
				  $avg_hum.",".
				  $avg_pres.",".
				  $avg_wind.",".
				  $avg_rain."\n";
	
	mysqli_free_result($result);
	
// get the accumulated rain
	$sql = "SELECT sum(Rainfall) as `total_rain` from `weather_data` WHERE Station_ID = '$st' and day(`Date`) = $day and month(`Date`) = $month and year(`Date`) = $year;";

	$result = $con->query($sql);
	while($row = $result->fetch_assoc()) {
		$total_rain  = $row["total_rain"];
	}

	mysqli_free_result($result);
	mysqli_close($con);

	echo $min_output;
	echo $max_output;
	echo $avg_output;
	echo $total_rain;
?>
