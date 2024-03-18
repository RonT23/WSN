<?php
	$conn = include 'connect.php';
	if (mysqli_connect_errno()) { exit(); } 
	
	$day   = date('d');
	$month = date('m');
	$year  = date('Y');
	
	$st = $_GET['st'];

	$sql = "SELECT * from `weather_data` WHERE Station_ID = '$st' and day(`Date`) = $day and month(`Date`) = $month and year(`Date`) = $year;";
	
	$result = mysqli_query($conn, $sql);
	while($row = mysqli_fetch_array($result, MYSQLI_NUM)){
							//id     //date    //time   //temp   //hum    //pres   //speed  //dir	 //rain
		printf ("%s,%s,%s,%s,%s,%s,%s,%s,%s\n", $row[0], $row[1], $row[2], $row[3], $row[4], $row[5], $row[6], $row[7], $row[8]);
	}

	mysqli_free_result($result);
	mysqli_close($conn);
?>
