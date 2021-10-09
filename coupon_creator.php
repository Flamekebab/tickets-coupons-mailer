<?php
//This script is to create coupons for a list of email addresses. This version applies to all complete roprey sets.


//We'll be pulling the following from the CSV for each person - although we'll only be creating coupons for unique email addresses.
//$unique_email, $firstName, $lastName
//We also need to check - we'll do party leaders first as they have priority when it comes to coupons
//The processed CSV file should be the argument at the command line (e.g. php coupon_creator.php output.csv)
//This'll mean that it's argument 1, not 0 (zero is this file - coupon_creator.php) - i.e. $argv[1]

$input_file = fopen($argv[1], 'r');

$input_data = [];

//feof opens a file and then reads lines until end of file (EOF) reached
while(! feof($input_file)){

	//fgetcsv() is a line-by-line thing because it's dumb.
	$line = fgetcsv($input_file);

	//Load that data into an array:
	$array_item = array("Prefix" => $line[0],
	"First" => $line[1],
	"Last" => $line[2],
	"Email" => strtolower($line[3]),
	"Phone" => $line[4],
	"Role" => $line[5],
	"Party Leader" => $line[6],
	"Party Size" => $line[7],
	"Bringing Falcons" => $line[8],
	"How many falcons?" => $line[9],
	"Flat race entries" => $line[10],
	"Hunt race entries" => $line[11],
	"Trader information" => $line[12],
	"Registration date" => $line[13]
	);
	array_push($input_data, $array_item);

}

//bin the first array item as it's the headers and the last one because it's nothing
array_shift($input_data);
array_pop($input_data);

fclose($input_file);


//We now need to divvy up the details. We'll create two arrays - party leaders and the party members
$party_leaders = [];
$party_members = [];

//Once they're done we'll compare the two and create a complete list
foreach ($input_data as $entry){
	//combine their first and last names to make a full name
	$entry_name = $entry['First']." ".$entry['Last'];
	//if their name is the same as their party leader then they're a party leader. Simple.
	if ($entry_name == $entry['Party Leader']){
	array_push($party_leaders,$entry);
	} else {
	//if it's not, they're a party member
	array_push($party_members,$entry);
	}
}

//Now we're going to create our list of unique people and email addresses.
$coupon_list = [];

//First we're going to grab the party leaders:
foreach ($party_leaders as $entry){
	//There could be duplicates because people fill in the form twice. Hopefully the input data is clean but let's not rely on it.
	//We grab just the party leader column from the coupon list and check whether this party leader is in there already. If they're not, we add them.
	if (! in_array($entry['Party Leader'], array_column($coupon_list, 'Party Leader')) ){
	array_push($coupon_list, $entry);
	}
}

//The coupon list now contains all our unique party leaders
//Now let's add in the party members with different email addresses. Duplicates don't get any.
foreach ($party_members as $entry){
        if (! in_array($entry['Email'], array_column($coupon_list, 'Email')) ){
        array_push($coupon_list, $entry);
        }
}

//So in principle we now have a list of unique email addresses and their associated details. Let's build some coupons!

//We'll need the username and password!
require_once("credentials.php");

// WooCommerce API library because ugh, cURL:
require __DIR__ . '/vendor/autoload.php';

use Automattic\WooCommerce\Client;

$woocommerce = new Client(
    'https://www.rofalconry.com', // Your store URL
    $user, // Your consumer key
    $password, // Your consumer secret
    [
        'wp_api' => true, // Enable the WP REST API integration
        'version' => 'wc/v3' // WooCommerce WP REST API version
    ]
);

//We should keep an easy list of the coupons we're creating:
$created_coupons = [];

//We also need to know which coupons already exist:
$existing_coupons = $woocommerce->get('coupons',["per_page" => 100]);
$existing_coupon_codes = array_column($existing_coupons, 'code');

//Now for the coupon creation:
foreach ($coupon_list as $coupon_details){

//to keep track of stuff we'll be constructing a simple object to stash the details:

$first_initial = substr($coupon_details['First'],0,1);

//Coupon code format: (first initial)(surname)"coupon" (capitalisation is ignored) (add an integer if necessary)

//Also strip spaces
$last_name_spaceless = str_replace(" ","",$coupon_details['Last']);

//That stash of details:
$created_coupon_details = array(
"coupon_code" => "{$first_initial}{$last_name_spaceless}coupon",
"email_address" => $coupon_details['Email'],
"first" => $coupon_details['First'],
"last" => $coupon_details['Last'],
);

//first off, what are the values?

$code = $created_coupon_details['coupon_code'];

//Is this code in there already?
if (in_array($code, array_column($created_coupons, 'coupon_code')) ){
//It is in the array already. We'll need a new code.

//count how many times it appears:
$array_count = array_count_values(array_column($created_coupons, 'coupon_code'));
//Use the code to find the value in the array of values array_count_values() returns
$count = $array_count[$code];

//Whilst we could make the number larger - why bother? Just append the count and that'll do!
$code = $code.$count;

//Also update the object we're creating with the relevant details
$created_coupon_details['coupon_code'] = $code;
}

array_push($created_coupons,$created_coupon_details);

$unique_email = $coupon_details['Email'];



//How much?
$amount = "100.00";

//You can provide a description if you like:
$description = "Coupon for {$coupon_details['First']} {$coupon_details['Last']} ({$unique_email})";

//When does this coupon expire?
$date_expires = "2020-10-01T00:00:00";


//It's relatively simple what needs doing. We're going to assemble an array and send that to the API
$data = array (
  'code' => $code,
  'email_restrictions' => array (
    0 => $unique_email,
  ),
  'date_expires' => $date_expires,
  'description' => $description,
  'amount' => '100.00',
  'discount_type' => 'fixed_cart',
  'individual_use' => true,
  'product_ids' =>
  array (
    0 => 271,
    1 => 320,
    2 => 319,
    3 => 347,
    4 => 338,
    5 => 350,
    6 => 346,
    7 => 349,
    8 => 348,
    9 => 304,
  ),
  'usage_limit' => 1,
  'usage_limit_per_user' => 1,
  'limit_usage_to_x_items' => 1,
  'free_shipping' => false,
  'exclude_sale_items' => false
);

//Now this coupon may already exist - if it does we don't need to create it.
//This is case sensitive whereas the data from the API is all lowercase - so ours need to be compared that way
if (! in_array(strtolower($code), $existing_coupon_codes)){
//The code doesn't exist yet, let's send it to the API:
print_r($woocommerce->post('coupons', $data));

//There's no "else" here because if the code already exists we just ignore the data we generated and do nothing with it - move on to the next entry!
}


}

//Debug
//var_dump($existing_coupon_codes);
var_dump($created_coupons);

//We've now created all those coupons, brilliant.
//We should probably output the info in some useful way, shouldn't we?
$created_coupons_file = fopen("created_coupons.txt", "w");
fwrite($created_coupons_file, json_encode($created_coupons));
fclose($created_coupons_file);
?>
