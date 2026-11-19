<?php
/* Servidor MCP de solo lectura · tuinversionendubai.com
   Transporte: Streamable HTTP (JSON-RPC 2.0 por POST, respuestas JSON). Sin sesión ni autenticación:
   solo expone contenido público de la web (las versiones index.md de cada página y el FAQ).
   Ficha pública: /.well-known/mcp/server-card.json */

const SERVER_NAME = 'tuinversionendubai';
const SERVER_VERSION = '1.0.0';
const PROTOCOLS = ['2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05'];
const SITE = 'https://tuinversionendubai.com';
define('DOCROOT', realpath(__DIR__ . '/..'));

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Accept, Mcp-Session-Id, MCP-Protocol-Version');
header('Access-Control-Expose-Headers: Mcp-Session-Id');
header('Cache-Control: no-store');
header('X-Robots-Tag: noindex');

$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
if ($method === 'OPTIONS') { http_response_code(204); exit; }
if ($method !== 'POST') {
  // Sin canal SSE: los clientes deben usar POST. Un GET desde el navegador recibe una explicación.
  http_response_code(405);
  header('Allow: POST, OPTIONS');
  header('Content-Type: application/json; charset=utf-8');
  echo json_encode(['error' => 'Servidor MCP (Streamable HTTP). Envía JSON-RPC por POST.', 'card' => SITE . '/.well-known/mcp/server-card.json'], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
  exit;
}

$raw = file_get_contents('php://input', false, null, 0, 65536);
$msg = json_decode($raw, true);
if (!is_array($msg)) reply(null, null, ['code' => -32700, 'message' => 'Parse error']);
if (array_is_list($msg)) reply(null, null, ['code' => -32600, 'message' => 'Batch no soportado']);

$id = $msg['id'] ?? null;
$rpc = $msg['method'] ?? '';
$params = is_array($msg['params'] ?? null) ? $msg['params'] : [];

// Notificaciones y respuestas del cliente: sin cuerpo
if (!array_key_exists('id', $msg)) { http_response_code(202); exit; }

switch ($rpc) {
  case 'initialize':
    $asked = $params['protocolVersion'] ?? '';
    reply($id, [
      'protocolVersion' => in_array($asked, PROTOCOLS, true) ? $asked : PROTOCOLS[1],
      'capabilities' => ['tools' => ['listChanged' => false]],
      'serverInfo' => ['name' => SERVER_NAME, 'title' => 'Tu inversión en Dubái · Pascual Vidal', 'version' => SERVER_VERSION],
      'instructions' => 'Información pública de Pascual Vidal, consultor inmobiliario español en Dubái (RERA #97799, Dubana Real Estate). '
        . 'Usa buscar o preguntas_frecuentes para dudas sobre invertir en Dubái, leer_pagina para el texto completo de una página, '
        . 'e info_negocio para datos de contacto. Contenido orientativo, no asesoramiento fiscal ni legal.',
    ]);
  case 'ping':
    reply($id, new stdClass());
  case 'tools/list':
    reply($id, ['tools' => tools()]);
  case 'tools/call':
    $name = $params['name'] ?? '';
    $args = is_array($params['arguments'] ?? null) ? $params['arguments'] : [];
    try {
      $out = call_tool($name, $args);
    } catch (InvalidArgumentException $e) {
      reply($id, null, ['code' => -32602, 'message' => $e->getMessage()]);
    } catch (Throwable $e) {
      reply($id, ['content' => [['type' => 'text', 'text' => 'Error: ' . $e->getMessage()]], 'isError' => true]);
    }
    $text = is_string($out) ? $out : json_encode($out, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
    $res = ['content' => [['type' => 'text', 'text' => $text]]];
    if (!is_string($out)) $res['structuredContent'] = $out;
    reply($id, $res);
  default:
    reply($id, null, ['code' => -32601, 'message' => 'Método no encontrado: ' . $rpc]);
}

/* ------------------------------------------------------------------ */

function reply($id, $result, $error = null) {
  header('Content-Type: application/json; charset=utf-8');
  $out = ['jsonrpc' => '2.0', 'id' => $id];
  if ($error) $out['error'] = $error; else $out['result'] = $result;
  echo json_encode($out, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
  exit;
}

function tools() {
  $ro = ['readOnlyHint' => true, 'openWorldHint' => false];
  return [
    ['name' => 'info_negocio', 'title' => 'Datos del negocio',
     'description' => 'Datos de contacto y servicios de Pascual Vidal · Tu inversión en Dubái: teléfono, WhatsApp, licencia RERA, agencia, idiomas, zonas y servicios.',
     'inputSchema' => ['type' => 'object', 'properties' => new stdClass()], 'annotations' => $ro],
    ['name' => 'preguntas_frecuentes', 'title' => 'Preguntas frecuentes',
     'description' => 'Preguntas frecuentes sobre invertir en Dubái (seguridad, costes, impuestos, compra en remoto, Golden Visa, alquiler). Filtra por texto opcional.',
     'inputSchema' => ['type' => 'object', 'properties' => ['buscar' => ['type' => 'string', 'description' => 'Texto a buscar en preguntas y respuestas (opcional)']]],
     'annotations' => $ro],
    ['name' => 'listar_paginas', 'title' => 'Listar páginas',
     'description' => 'Lista las páginas y guías del blog de la web con su URL y título.',
     'inputSchema' => ['type' => 'object', 'properties' => new stdClass()], 'annotations' => $ro],
    ['name' => 'leer_pagina', 'title' => 'Leer página',
     'description' => 'Devuelve en Markdown el contenido de una página de tuinversionendubai.com (por ejemplo /blog/golden-visa-dubai-inversion-inmobiliaria/).',
     'inputSchema' => ['type' => 'object', 'required' => ['url'], 'properties' => ['url' => ['type' => 'string', 'description' => 'URL completa o ruta de la página, p. ej. /contacto/']]],
     'annotations' => $ro],
    ['name' => 'buscar', 'title' => 'Buscar en la web',
     'description' => 'Busca un término en todas las páginas y guías (zonas, costes, impuestos, Golden Visa, países…) y devuelve las páginas que lo mencionan con un extracto.',
     'inputSchema' => ['type' => 'object', 'required' => ['consulta'], 'properties' => ['consulta' => ['type' => 'string', 'description' => 'Palabras a buscar']]],
     'annotations' => $ro],
  ];
}

function call_tool($name, $a) {
  switch ($name) {
    case 'info_negocio': return info();
    case 'preguntas_frecuentes': return faq(trim((string)($a['buscar'] ?? '')));
    case 'listar_paginas': return pages();
    case 'leer_pagina':
      $u = trim((string)($a['url'] ?? ''));
      if ($u === '') throw new InvalidArgumentException('Falta "url"');
      return read_page($u);
    case 'buscar':
      $q = trim((string)($a['consulta'] ?? ''));
      if (mb_strlen($q) < 2) throw new InvalidArgumentException('La consulta debe tener al menos 2 caracteres');
      return search($q);
  }
  throw new InvalidArgumentException('Herramienta desconocida: ' . $name);
}

function info() {
  return [
    'nombre' => 'Tu inversión en Dubái · Pascual Vidal',
    'descripcion' => 'Consultoría de inversión inmobiliaria en Dubái para hispanohablantes: obra nueva y segunda mano, compra en remoto, postventa, amueblado, alquiler vacacional y anual, reventa y Golden Visa.',
    'consultor' => 'Pascual Vidal, consultor inmobiliario español registrado en el Dubai Land Department (RERA n.º 97799)',
    'agencia' => 'Dubana Real Estate (Dubái, EAU)',
    'telefono' => '+971507963006',
    'whatsapp' => 'https://wa.me/message/QI3A7Q5BXFTCA1',
    'contacto' => SITE . '/contacto/',
    'consultoria_gratuita' => SITE . '/consultoria/',
    'guia_gratuita' => SITE . '/guia/',
    'idiomas' => ['español', 'inglés'],
    'zonas' => ['Dubái', 'Abu Dabi', 'Ras Al Khaimah'],
    'redes' => ['https://www.instagram.com/pascual.dubairealestate/', 'https://www.youtube.com/@pascual.dubairealestate'],
  ];
}

function faq($q) {
  $html = @file_get_contents(DOCROOT . '/index.html');
  $items = [];
  if ($html && preg_match_all('#<script type="application/ld\+json">(.*?)</script>#s', $html, $m)) {
    foreach ($m[1] as $j) {
      $d = json_decode($j, true);
      if (($d['@type'] ?? '') !== 'FAQPage') continue;
      foreach ($d['mainEntity'] as $e) $items[] = ['pregunta' => $e['name'], 'respuesta' => $e['acceptedAnswer']['text']];
    }
  }
  if ($q !== '') $items = array_values(array_filter($items, fn($i) => mb_stripos($i['pregunta'] . ' ' . $i['respuesta'], $q) !== false));
  return ['preguntas' => $items, 'fuente' => SITE . '/#preguntas'];
}

function md_files() {
  $out = [];
  $it = new RecursiveIteratorIterator(new RecursiveDirectoryIterator(DOCROOT, FilesystemIterator::SKIP_DOTS));
  foreach ($it as $f) {
    if ($f->getFilename() !== 'index.md') continue;
    $rel = substr($f->getPath(), strlen(DOCROOT));
    if (preg_match('#^/(crm|tools|\.git|assets)(/|$)#', $rel)) continue;
    $out[($rel === '' ? '' : $rel) . '/'] = $f->getPathname();
  }
  ksort($out);
  return $out;
}

function front($text, $key) {
  return preg_match('/^' . $key . ': (.*)$/m', $text, $m) ? trim($m[1]) : '';
}

function pages() {
  $list = [];
  foreach (md_files() as $path => $file) {
    $t = file_get_contents($file, false, null, 0, 2048);
    $list[] = ['url' => SITE . $path, 'titulo' => front($t, 'title'), 'descripcion' => front($t, 'description')];
  }
  return ['paginas' => $list];
}

function read_page($u) {
  $path = parse_url($u, PHP_URL_PATH) ?: '/';
  $path = '/' . trim($path, '/');
  $path = $path === '/' ? '/' : $path . '/';
  $files = md_files();
  if (!isset($files[$path])) throw new InvalidArgumentException('Página no encontrada: ' . $path . '. Usa listar_paginas.');
  return file_get_contents($files[$path]);
}

function search($q) {
  $hits = [];
  foreach (md_files() as $path => $file) {
    $t = file_get_contents($file);
    $pos = mb_stripos($t, $q);
    if ($pos === false) continue;
    $n = mb_substr_count(mb_strtolower($t), mb_strtolower($q));
    $start = max(0, $pos - 160);
    $snip = trim(preg_replace('/\s+/', ' ', mb_substr($t, $start, 360)));
    $hits[] = ['url' => SITE . $path, 'titulo' => front($t, 'title'), 'coincidencias' => $n, 'extracto' => ($start ? '…' : '') . $snip . '…'];
  }
  usort($hits, fn($a, $b) => $b['coincidencias'] <=> $a['coincidencias']);
  return ['consulta' => $q, 'resultados' => array_slice($hits, 0, 8)];
}
