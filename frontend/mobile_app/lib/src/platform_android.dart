// Android platform helper. This file should only be imported on Android builds.
import 'dart:io' show Platform;

bool get isAndroid => Platform.isAndroid;
String get defaultHost => 'localhost';
