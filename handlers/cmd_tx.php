<?php
	$station_id = $_GET['st'];
	$filepath = "./command_files/cmd_".$station_id;
	$cmd = file_get_contents($filepath, "r");
	echo $cmd;
?>
