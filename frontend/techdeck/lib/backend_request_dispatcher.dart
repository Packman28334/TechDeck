
import 'dart:convert';

import 'package:http/http.dart' as http;

String _getIP() {
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
  http.Response response = await http.get(Uri.http(_getIP(), route));
  return jsonDecode(response.body) as Map<String, dynamic>;
}