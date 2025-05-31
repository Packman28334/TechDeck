
import 'dart:convert';

import 'package:http/http.dart' as http;

String getIP() {
  String ip = String.fromEnvironment("IP");
  if (ip == "") {
    print("Using default backend IP");
    return "localhost:8383"; // TODO: change back to 10.72.2.102:8383
  } else{
    print("Using $ip as backend IP");
    return "$ip:8383";
  }
}

Future<Map<String, dynamic>> get(String route) async {
  print("Sending GET request to $route");
  http.Response response = await http.get(Uri.http(getIP(), route));
  if (response.body == "null") {
    return <String, dynamic>{"_success": true};
  } else if (response.body == "Internal Server Error" || response.statusCode != 200) {
    return <String, dynamic>{"_success": false};
  }
  Map<String, dynamic> out = jsonDecode(response.body) as Map<String, dynamic>;
  out["_success"] = true;
  return out;
}

Future<Map<String, dynamic>> post(String route, Map<String, dynamic> body) async { // untested
  print("Sending POST request to $route");
  http.Response response = await http.post(
    Uri.http(getIP(), route),
    body: body,
    headers: Map<String, String>.fromIterables(["Content-Type"], ["application/json"])
  );
  if (response.body == "null") {
    return <String, dynamic>{"_success": true};
  } else if (response.body == "Internal Server Error" || response.statusCode != 200) {
    return <String, dynamic>{"_success": false};
  }
  Map<String, dynamic> out = jsonDecode(response.body) as Map<String, dynamic>;
  out["_success"] = true;
  return out;
}