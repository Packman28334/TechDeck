
import 'package:http/http.dart';

String _getIP() {
  String ip = String.fromEnvironment("ip");
  if (ip == "") {
    ip = "10.72.2.102";
  }
  return ip;
}

