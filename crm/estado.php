<?php
/* Diagnóstico temporal del CRM: no muestra datos, solo si el servidor cumple los requisitos. */
header('Content-Type: text/plain; charset=utf-8');
header('X-Robots-Tag: noindex');
$ok = function ($b) { return $b ? 'OK' : 'FALLA'; };
echo "PHP " . PHP_VERSION . " · " . $ok(version_compare(PHP_VERSION, '7.3', '>=')) . "\n";
$out = dirname(__DIR__, 2) . '/crm-data';
$canOut = (@is_dir($out) || @mkdir($out, 0700, true)) && @is_writable($out);
echo "Carpeta privada fuera de la web: " . $ok($canOut) . "\n";
echo "Carpeta /crm escribible: " . $ok(is_writable(__DIR__)) . "\n";
echo "json: " . $ok(function_exists('json_encode')) . " · sesiones: " . $ok(function_exists('session_start')) . " · curl: " . $ok(function_exists('curl_init')) . " · mbstring: " . $ok(function_exists('mb_substr')) . "\n";
echo "Fin del diagnóstico.\n";
