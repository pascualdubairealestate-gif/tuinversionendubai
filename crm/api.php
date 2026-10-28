<?php
/* CRM · API. Pública solo `lead` (formularios de la web); el resto exige sesión + token CSRF. */
require __DIR__ . '/lib.php';

$action = $_GET['action'] ?? '';
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';

function body() {
  static $b = null;
  if ($b === null) {
    $raw = (string) file_get_contents('php://input', false, null, 0, 65536);
    $b = json_decode($raw, true);
    if (!is_array($b)) $b = $_POST ?: [];
  }
  return $b;
}

function require_auth($write = true) {
  if (!authed()) json_out(['error' => 'auth'], 401);
  if ($write) {
    $t = $_SERVER['HTTP_X_CSRF'] ?? '';
    if (!$t || !hash_equals(csrf(), $t)) json_out(['error' => 'csrf'], 403);
  }
}

/* ---------- Entrada pública: formularios de la web ---------- */
if ($action === 'lead') {
  if ($method === 'OPTIONS') { http_response_code(204); exit; }
  if ($method !== 'POST') json_out(['error' => 'method'], 405);
  $b = body();
  if (!empty($b['web'])) json_out(['ok' => true]); // honeypot: bots
  $email = strtolower(cut($b['email'] ?? '', 160));
  $tel = cut($b['telefono'] ?? '', 40);
  if (!filter_var($email, FILTER_VALIDATE_EMAIL) && strlen(phone_digits($tel)) < 7) json_out(['error' => 'datos'], 422);
  if (!rate('lead', 20, 3600)) json_out(['error' => 'rate'], 429);

  $forms = ['guia' => 'Web · Guía', 'newsletter' => 'Web · Boletín', 'consultoria' => 'Web · Consultoría', 'dossier' => 'Web · Dossier'];
  $form = cut($b['formulario'] ?? 'web', 30);
  $origen = $forms[$form] ?? 'Web';
  $utm = [];
  foreach (['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'gclid', 'fbclid'] as $k) {
    if (!empty($b[$k])) $utm[$k] = cut($b[$k], 200);
  }

  $res = with_lock('leads', function () use ($b, $email, $tel, $form, $origen, $utm) {
    $leads = store_read('leads', []);
    $idx = null;
    foreach ($leads as $i => $l) {
      if (($email && $l['email'] === $email) || (strlen(phone_digits($tel)) >= 7 && phone_digits($l['telefono']) === phone_digits($tel))) { $idx = $i; break; }
    }
    $isNew = $idx === null;
    $lead = $isNew ? blank_lead() : $leads[$idx];
    // Completa solo los campos vacíos: no pisa lo que ya editaste a mano.
    foreach (['nombre', 'telefono', 'presupuesto', 'objetivo', 'proyecto'] as $f) {
      $v = cut($b[$f] ?? '', FIELDS[$f]);
      if ($v !== '' && ($lead[$f] ?? '') === '') $lead[$f] = $v;
    }
    if ($email && !$lead['email']) $lead['email'] = $email;
    if ($isNew) { $lead['origen'] = $origen; $lead['utm'] = $utm; }
    if ($form === 'newsletter') $lead['boletin'] = true;
    $tags = array_filter(array_map('trim', explode(',', $lead['etiquetas'] ?? '')));
    $tag = strtolower(str_replace('Web · ', '', $origen));
    if (!in_array($tag, $tags, true)) $tags[] = $tag;
    $lead['etiquetas'] = cut(implode(', ', $tags), FIELDS['etiquetas']);
    $txt = ($isNew ? 'Nuevo lead desde ' : 'Ha vuelto a escribir: ') . $origen;
    if (!empty($b['proyecto'])) $txt .= ' (' . cut($b['proyecto'], 120) . ')';
    if (!empty($b['mensaje'])) $txt .= "\n«" . cut($b['mensaje'], 2000) . '»';
    if ($utm) $txt .= "\nCampaña: " . implode(' · ', $utm);
    activity($lead, $txt, 'web');
    $lead['actualizado'] = now_iso();
    $lead['nuevo'] = true;
    if ($isNew) $leads[] = $lead; else $leads[$idx] = $lead;
    store_write('leads', $leads);
    return [$lead, $txt];
  });

  $notify = config()['notify'] ?? '';
  if ($notify && function_exists('mail')) {
    [$lead, $txt] = $res;
    $host = preg_replace('/[^a-z0-9.-]/i', '', $_SERVER['HTTP_HOST'] ?? 'localhost');
    $host = preg_replace('/^www\./', '', $host);
    $msg = "Nombre: {$lead['nombre']}\nEmail: {$lead['email']}\nTeléfono: {$lead['telefono']}\n\n$txt\n\nAbrir CRM: https://$host/crm/";
    $subj = '=?UTF-8?B?' . base64_encode('Nuevo lead: ' . ($lead['nombre'] ?: $lead['email'])) . '?=';
    @mail($notify, $subj, $msg, "From: CRM <noreply@$host>\r\nContent-Type: text/plain; charset=UTF-8");
  }
  json_out(['ok' => true]);
}

/* ---------- Panel ---------- */
if ($action === 'state') {
  require_auth(false);
  $cfg = config();
  json_out(['leads' => store_read('leads', []), 'stages' => STAGES, 'notify' => $cfg['notify'] ?? '', 'ics' => $cfg['ics'] ?? '', 'csrf' => csrf()]);
}

if ($action === 'save' && $method === 'POST') {
  require_auth();
  $b = body();
  $patch = is_array($b['patch'] ?? null) ? $b['patch'] : [];
  $id = (string) ($b['id'] ?? '');
  $lead = with_lock('leads', function () use ($id, $patch) {
    $leads = store_read('leads', []);
    foreach ($leads as $i => $l) {
      if ($l['id'] === $id) {
        $leads[$i] = apply_patch($l, $patch);
        unset($leads[$i]['nuevo']);
        store_write('leads', $leads);
        return $leads[$i];
      }
    }
    if ($id !== '') return null;
    $l = blank_lead();
    $l['origen'] = 'Manual';
    $l = apply_patch($l, $patch);
    activity($l, 'Lead creado a mano');
    $leads[] = $l;
    store_write('leads', $leads);
    return $l;
  });
  if (!$lead) json_out(['error' => 'no existe'], 404);
  json_out(['lead' => $lead]);
}

if ($action === 'seen' && $method === 'POST') {
  require_auth();
  $id = (string) (body()['id'] ?? '');
  with_lock('leads', function () use ($id) {
    $leads = store_read('leads', []);
    foreach ($leads as $i => $l) if ($l['id'] === $id && !empty($l['nuevo'])) { unset($leads[$i]['nuevo']); store_write('leads', $leads); }
  });
  json_out(['ok' => true]);
}

if ($action === 'delete' && $method === 'POST') {
  require_auth();
  $id = (string) (body()['id'] ?? '');
  with_lock('leads', function () use ($id) {
    $leads = store_read('leads', []);
    store_write('leads', array_values(array_filter($leads, function ($l) use ($id) { return $l['id'] !== $id; })));
  });
  json_out(['ok' => true]);
}

if ($action === 'settings' && $method === 'POST') {
  require_auth();
  $b = body();
  $res = with_lock('config', function () use ($b) {
    $cfg = config();
    if (array_key_exists('notify', $b)) {
      $n = cut($b['notify'], 160);
      if ($n !== '' && !filter_var($n, FILTER_VALIDATE_EMAIL)) return ['error' => 'Email de aviso no válido'];
      $cfg['notify'] = $n;
    }
    if (array_key_exists('ics', $b)) {
      $u = trim((string) $b['ics']);
      $u = preg_replace('#^webcal://#i', 'https://', $u);
      if ($u !== '' && !preg_match('#^https://[^\s]+$#i', $u)) return ['error' => 'La dirección de Google Calendar debe empezar por https://'];
      $cfg['ics'] = cut($u, 600);
    }
    if (!empty($b['nueva'])) {
      if (!password_verify((string) ($b['actual'] ?? ''), $cfg['hash'])) return ['error' => 'La contraseña actual no es correcta'];
      if (strlen((string) $b['nueva']) < 10) return ['error' => 'La nueva contraseña necesita al menos 10 caracteres'];
      $cfg['hash'] = password_hash((string) $b['nueva'], PASSWORD_DEFAULT);
      $cfg['v'] = bin2hex(random_bytes(8)); // cierra las demás sesiones
    }
    store_write('config', $cfg);
    return ['ok' => true];
  });
  if (!empty($res['ok']) && !empty($b['nueva'])) login_session();
  json_out($res + ['csrf' => csrf()], empty($res['ok']) ? 422 : 200);
}

if ($action === 'export') {
  require_auth(false);
  $leads = store_read('leads', []);
  $fmt = $_GET['fmt'] ?? 'csv';
  $stamp = date('Y-m-d');
  if ($fmt === 'json') {
    header('Content-Type: application/json; charset=utf-8');
    header("Content-Disposition: attachment; filename=\"crm-copia-$stamp.json\"");
    echo json_encode($leads, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
  }
  $onlyNl = ($_GET['solo'] ?? '') === 'boletin';
  header('Content-Type: text/csv; charset=utf-8');
  header('Content-Disposition: attachment; filename="' . ($onlyNl ? 'boletin' : 'leads') . "-$stamp.csv\"");
  $out = fopen('php://output', 'w');
  fwrite($out, "\xEF\xBB\xBF"); // BOM para que Excel lea los acentos
  $cols = ['nombre', 'email', 'telefono', 'pais', 'etapa', 'origen', 'presupuesto', 'objetivo', 'proyecto', 'valor', 'proxima_accion', 'seguimiento', 'etiquetas', 'boletin', 'creado'];
  fputcsv($out, $cols, ';');
  foreach ($leads as $l) {
    if ($onlyNl && empty($l['boletin'])) continue;
    $row = [];
    foreach ($cols as $c) {
      $v = $c === 'etapa' ? (STAGES[$l['etapa']] ?? $l['etapa']) : ($c === 'boletin' ? (!empty($l['boletin']) ? 'sí' : 'no') : (string) ($l[$c] ?? ''));
      if ($v !== '' && strpos('=+-@', $v[0]) !== false) $v = "'" . $v; // evita fórmulas en Excel
      $row[] = $v;
    }
    fputcsv($out, $row, ';');
  }
  exit;
}

/* ---------- Calendario (Google Calendar vía iCal privado) ---------- */
if ($action === 'calendar') {
  require_auth(false);
  $url = config()['ics'] ?? '';
  if (!$url) json_out(['eventos' => [], 'conectado' => false]);
  $tz = ics_tz((string) ($_GET['tz'] ?? 'UTC'));
  $from = DateTime::createFromFormat('Y-m-d H:i:s', ($_GET['from'] ?? '') . ' 00:00:00', $tz) ?: new DateTime('today -1 day', $tz);
  $to = DateTime::createFromFormat('Y-m-d H:i:s', ($_GET['to'] ?? '') . ' 23:59:59', $tz) ?: new DateTime('+45 days', $tz);
  if ($to->getTimestamp() - $from->getTimestamp() > 400 * 86400) json_out(['error' => 'rango'], 422);
  $raw = ics_source($url);
  if ($raw === null) json_out(['eventos' => [], 'conectado' => true, 'error' => 'No se pudo leer tu Google Calendar. Revisa la dirección iCal en Ajustes.']);
  json_out(['eventos' => ics_events($raw, $from->getTimestamp(), $to->getTimestamp(), $tz), 'conectado' => true]);
}

/* ---------- Plantillas de correo ---------- */
if ($action === 'templates') {
  require_auth(false);
  json_out(['plantillas' => store_read('plantillas', default_templates())]);
}

if ($action === 'tpl_save' && $method === 'POST') {
  require_auth();
  $b = body();
  $list = with_lock('plantillas', function () use ($b) {
    $list = store_read('plantillas', default_templates());
    $t = ['id' => cut($b['id'] ?? '', 20) ?: 't' . bin2hex(random_bytes(4)), 'nombre' => cut($b['nombre'] ?? '', 120) ?: 'Sin nombre', 'asunto' => cut($b['asunto'] ?? '', 200), 'cuerpo' => cut($b['cuerpo'] ?? '', 8000)];
    $found = false;
    foreach ($list as $i => $x) if ($x['id'] === $t['id']) { $list[$i] = $t; $found = true; }
    if (!empty($b['borrar'])) $list = array_values(array_filter($list, function ($x) use ($t) { return $x['id'] !== $t['id']; }));
    elseif (!$found) $list[] = $t;
    store_write('plantillas', $list);
    return $list;
  });
  json_out(['plantillas' => $list]);
}

/* ---------- Documentos ---------- */
if ($action === 'docs') {
  require_auth(false);
  json_out(['docs' => store_read('docs', [])]);
}

if ($action === 'upload' && $method === 'POST') {
  require_auth();
  $f = $_FILES['file'] ?? null;
  if (!$f || $f['error'] !== UPLOAD_ERR_OK || !is_uploaded_file($f['tmp_name'])) {
    json_out(['error' => ($f && in_array($f['error'], [UPLOAD_ERR_INI_SIZE, UPLOAD_ERR_FORM_SIZE], true)) ? 'Archivo demasiado grande' : 'No se pudo subir el archivo'], 422);
  }
  $name = cut(basename(str_replace('\\', '/', $f['name'])), 160);
  $ext = strtolower(pathinfo($name, PATHINFO_EXTENSION));
  if (!in_array($ext, DOC_EXT, true)) json_out(['error' => 'Tipo de archivo no permitido (.' . $ext . ')'], 422);
  if ($f['size'] > DOC_MAX) json_out(['error' => 'Máximo 25 MB por archivo'], 422);
  $id = 'd' . bin2hex(random_bytes(8));
  if (!move_uploaded_file($f['tmp_name'], docs_dir() . '/' . $id)) json_out(['error' => 'No se pudo guardar'], 500);
  $doc = ['id' => $id, 'nombre' => $name, 'ext' => $ext, 'tamano' => (int) $f['size'], 'lead' => cut($_POST['lead'] ?? '', 40), 'creado' => now_iso()];
  with_lock('docs', function () use ($doc) { $d = store_read('docs', []); $d[] = $doc; store_write('docs', $d); });
  json_out(['doc' => $doc]);
}

if ($action === 'doc_update' && $method === 'POST') {
  require_auth();
  $b = body();
  $id = (string) ($b['id'] ?? '');
  $list = with_lock('docs', function () use ($b, $id) {
    $d = store_read('docs', []);
    foreach ($d as $i => $x) {
      if ($x['id'] !== $id) continue;
      if (!empty($b['borrar'])) { @unlink(docs_dir() . '/' . $x['id']); unset($d[$i]); }
      elseif (array_key_exists('lead', $b)) $d[$i]['lead'] = cut($b['lead'], 40);
    }
    $d = array_values($d);
    store_write('docs', $d);
    return $d;
  });
  json_out(['docs' => $list]);
}

if ($action === 'doc') {
  require_auth(false);
  $id = (string) ($_GET['id'] ?? '');
  foreach (store_read('docs', []) as $x) {
    if ($x['id'] !== $id || !preg_match('/^d[0-9a-f]{16}$/', $id)) continue;
    $path = docs_dir() . '/' . $id;
    if (!is_file($path)) break;
    $types = ['pdf' => 'application/pdf', 'jpg' => 'image/jpeg', 'jpeg' => 'image/jpeg', 'png' => 'image/png', 'webp' => 'image/webp', 'mp4' => 'video/mp4', 'txt' => 'text/plain; charset=utf-8'];
    $inline = isset($types[$x['ext']]) && empty($_GET['dl']);
    header('Content-Type: ' . ($types[$x['ext']] ?? 'application/octet-stream'));
    header('X-Content-Type-Options: nosniff');
    header("Content-Security-Policy: default-src 'none'; img-src 'self'; media-src 'self'; style-src 'unsafe-inline'; sandbox");
    header('Content-Length: ' . filesize($path));
    header('Content-Disposition: ' . ($inline ? 'inline' : 'attachment') . "; filename*=UTF-8''" . rawurlencode($x['nombre']));
    header('Cache-Control: private, no-store');
    readfile($path);
    exit;
  }
  http_response_code(404);
  exit('No encontrado');
}

json_out(['error' => 'acción desconocida'], 404);
