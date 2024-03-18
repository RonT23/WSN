<?php
	$station_id = $_GET['id'];
	$cmd_id     = $_GET['cmd'];
	$arg        = $_GET['arg'];
	
	$cmd = "$".$cmd_id.", ".$arg."$";

	$filePath = "./command_files/cmd_".$station_id;

	$fp1 = fopen($filePath, 'w');
	fwrite($fp1,$cmd);
	fclose($fp1);

	echo $cmd;
?>
