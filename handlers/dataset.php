<?php
	$conn = include 'connect.php';
	if (mysqli_connect_errno()) { exit(); } 
	
	$st = $_GET['st'];

	$from_day   = $_GET['from_day'];
	$from_month = $_GET['from_month'];
	$from_year  = $_GET['from_year'];

	$to_day     = $_GET['to_day'];
	$to_month   = $_GET['to_month'];
	$to_year    = $_GET['to_year'];

	$sql = "SELECT * FROM `weather_data` WHERE Station_ID = '$st' and 
	day(`Date`) >= $from_day and day(`Date`) <= $to_day and
	month(`Date`) >= $from_month and month(`Date`) <= $to_month and
	year(`Date`) >= $from_year and year(`Date`) = $to_year;";

	$result = mysqli_query($conn, $sql);

	while($row = mysqli_fetch_array($result, MYSQLI_NUM)){
		printf ("%s,%s,%s,%s,%s,%s,%s,%s,%s\n", $row[0], $row[1], $row[2], $row[3], $row[4], $row[5], $row[6], $row[7], $row[8]);
	}

	mysqli_free_result($result);
	mysqli_close($conn);
?>
