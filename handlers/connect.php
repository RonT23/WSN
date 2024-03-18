<?php
	// **** specify this for your server **** //
	
	$host = 'host';	 // enter the host here
	$user = 'user';	 // enter the user here 
	$pswd = 'pswd';  // enter the password here
	$dbnm = 'dbnm';  // enter the database name here
	
	// ************************************** //
	
	$conn = mysqli_connect($host, $user, $pswd, $dbnm);
	
	return $conn;
?>
