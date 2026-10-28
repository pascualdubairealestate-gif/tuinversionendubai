<?php
/* ============================================================================
   CRM · Tu inversión en Dubái — almacenamiento, sesión y utilidades.
   Sin base de datos: ficheros JSON protegidos (cabecera PHP que corta la
   ejecución) guardados FUERA de public_html para que sobrevivan a cada deploy.
   ============================================================================ */
if (realpath($_SERVER['SCRIPT_FILENAME'] ?? '') === __FILE__) { http_response_code(404); exit; }

const STAGES = [
  'lead'        => 'Lead',
  'qualified'   => 'Qualified',
  'opportunity' => 'Opportunity',
  'customer'    => 'Customer',
  'nurturing'   => 'Nurturing',
];
const FIELDS = [
  'nombre' => 120, 'email' => 160, 'telefono' => 40, 'pais' => 60, 'origen' => 60,
  'presupuesto' => 60, 'objetivo' => 80, 'proyecto' => 120, 'valor' => 20,
  'proxima_accion' => 200, 'seguimiento' => 10, 'etiquetas' => 200,
];
// Ventas: datos de la operación y sus hitos, en orden (cada hito guarda la fecha en que se cumplió).
const SALE_FIELDS = [
  'lead' => 40, 'proyecto' => 120, 'unidad' => 60, 'promotor' => 80,
  'precio' => 20, 'comision' => 20, 'inicio' => 10, 'notas' => 2000,
];
const HITOS = [
  'inicio'  => 'EOI / Reserva',
  'booking' => 'Booking form',
  'spa'     => 'SPA firmado',
  'oqood'   => 'Oqood registrado',
  'factura' => 'Factura enviada',
  'cobrada' => 'Comisión recibida',
  'pagado'  => 'Pagado',
];
// SHA-256 de la clave de instalación (un solo uso, se entregó por privado).
const SETUP_KEY_HASH = 'c2005a8bdcd61388aa3f5633b8dc5d987884fa217882d3a17b61987f46fcf27d';
const GUARD = "<?php http_response_code(404); exit; ?>\n";

function crm_dir() {
  static $dir = null;
  if ($dir) return $dir;
  // 1) Fuera de la web: /home/uXXX/domains/tudominio.com/crm-data
  $out = dirname(__DIR__, 2) . '/crm-data';
  if ((@is_dir($out) || @mkdir($out, 0700, true)) && @is_writable($out)) return $dir = $out;
  // 2) Respaldo: carpeta protegida dentro de /crm
  $in = __DIR__ . '/data';
  if (!is_dir($in)) @mkdir($in, 0700, true);
  if (!is_file("$in/.htaccess")) {
    @file_put_contents("$in/.htaccess", "<IfModule mod_authz_core.c>\n  Require all denied\n</IfModule>\n<IfModule !mod_authz_core.c>\n  Deny from all\n</IfModule>\n");
  }
  if (!is_file("$in/index.html")) @file_put_contents("$in/index.html", '');
  return $dir = $in;
}

function store_read($name, $default = []) {
  $f = crm_dir() . "/$name.php";
  if (!is_file($f)) return $default;
  $data = json_decode(substr((string) file_get_contents($f), strlen(GUARD)), true);
  return is_array($data) ? $data : $default;
}

function store_write($name, $data) {
  $f = crm_dir() . "/$name.php";
  $tmp = crm_dir() . "/.$name-" . bin2hex(random_bytes(4)) . '.php';
  $json = json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
  if ($json === false || file_put_contents($tmp, GUARD . $json, LOCK_EX) === false) {
    throw new RuntimeException('No se pudo guardar');
  }
  rename($tmp, $f);
}

// Exclusión mutua para leer-modificar-escribir. Un candado por fichero: no anidar el mismo.
function with_lock($name, callable $fn) {
  $h = fopen(crm_dir() . "/.$name.lock", 'c');
  flock($h, LOCK_EX);
  try { return $fn(); } finally { flock($h, LOCK_UN); fclose($h); }
}

/* ---------- Sesión ---------- */
function crm_base() {
  return rtrim(str_replace('\\', '/', dirname($_SERVER['SCRIPT_NAME'] ?? '/crm/x')), '/') . '/';
}

function crm_session() {
  if (session_status() === PHP_SESSION_ACTIVE) return;
  $days = 30 * 86400;
  $path = crm_dir() . '/sessions';
  if (!is_dir($path)) @mkdir($path, 0700, true);
  if (is_writable($path)) session_save_path($path);
  ini_set('session.gc_maxlifetime', (string) $days);
  ini_set('session.use_strict_mode', '1');
  session_name('pvcrm');
  session_set_cookie_params([
    'lifetime' => $days, 'path' => crm_base(), 'httponly' => true, 'samesite' => 'Strict',
    'secure' => (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https'),
  ]);
  session_start();
}

function config() { return store_read('config', []); }
function is_setup() { return !empty(config()['hash']); }

function authed() {
  crm_session();
  $cfg = config();
  return !empty($_SESSION['ok']) && !empty($cfg['v']) && hash_equals($cfg['v'], (string) ($_SESSION['v'] ?? ''));
}

function login_session() {
  crm_session();
  session_regenerate_id(true);
  $_SESSION['ok'] = 1;
  $_SESSION['v'] = config()['v'];
  $_SESSION['csrf'] = bin2hex(random_bytes(16));
}

function csrf() { crm_session(); return $_SESSION['csrf'] ?? ''; }

/* ---------- Límite de intentos por IP ---------- */
function rate($bucket, $max, $window, $add = true) {
  $key = $bucket . ':' . substr(hash('sha256', ($_SERVER['REMOTE_ADDR'] ?? '0') . 'pv'), 0, 20);
  return with_lock('rate', function () use ($key, $max, $window, $add) {
    $now = time();
    $all = store_read('rate', []);
    foreach ($all as $k => $hits) {
      $all[$k] = array_values(array_filter($hits, function ($t) use ($now) { return $t > $now - 86400; }));
      if (!$all[$k]) unset($all[$k]);
    }
    $recent = array_filter($all[$key] ?? [], function ($t) use ($now, $window) { return $t > $now - $window; });
    $ok = count($recent) < $max;
    if ($ok && $add) $all[$key][] = $now;
    store_write('rate', $all);
    return $ok;
  });
}

/* ---------- Leads ---------- */
function cut($s, $n) {
  $s = trim(is_scalar($s) ? (string) $s : '');
  return function_exists('mb_substr') ? mb_substr($s, 0, $n) : substr($s, 0, $n);
}

function new_id() { return 'l' . base_convert((string) time(), 10, 36) . bin2hex(random_bytes(3)); }
function now_iso() { return gmdate('c'); }

function activity(array &$lead, $texto, $tipo = 'sistema') {
  $lead['actividad'][] = ['fecha' => now_iso(), 'tipo' => $tipo, 'texto' => cut($texto, 4000)];
}

// Aplica un parche de campos editables; registra los cambios de etapa.
function apply_patch(array $lead, array $patch) {
  foreach (FIELDS as $f => $max) {
    if (array_key_exists($f, $patch)) $lead[$f] = cut($patch[$f], $max);
  }
  if (array_key_exists('boletin', $patch)) $lead['boletin'] = (bool) $patch['boletin'];
  if (isset($patch['etapa']) && isset(STAGES[$patch['etapa']]) && $patch['etapa'] !== ($lead['etapa'] ?? '')) {
    $from = STAGES[$lead['etapa'] ?? 'lead'] ?? '—';
    if (!empty($lead['etapa'])) activity($lead, "Etapa: $from → " . STAGES[$patch['etapa']], 'etapa');
    $lead['etapa'] = $patch['etapa'];
  }
  if (!empty($patch['nota'])) activity($lead, $patch['nota'], 'nota');
  $lead['email'] = strtolower($lead['email'] ?? '');
  $lead['actualizado'] = now_iso();
  return $lead;
}

function blank_lead() {
  $l = array_fill_keys(array_keys(FIELDS), '');
  return $l + ['id' => new_id(), 'etapa' => 'lead', 'boletin' => false, 'actividad' => [], 'utm' => [], 'creado' => now_iso(), 'actualizado' => now_iso()];
}

function phone_digits($p) { return preg_replace('/\D+/', '', (string) $p); }

function json_out($data, $code = 200) {
  http_response_code($code);
  header('Content-Type: application/json; charset=utf-8');
  header('Cache-Control: no-store');
  echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
  exit;
}

function h($s) { return htmlspecialchars((string) $s, ENT_QUOTES, 'UTF-8'); }

/* ---------- Documentos ---------- */
const DOC_EXT = ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'webp', 'heic', 'txt', 'csv', 'zip', 'mp4', 'mov'];
const DEFAULT_FOLDERS = ['DUBANA', 'GUÍAS', 'OQOODs', 'SPAs'];
const DOC_MAX = 25 * 1024 * 1024;
function docs_dir() {
  $d = crm_dir() . '/docs';
  if (!is_dir($d)) @mkdir($d, 0700, true);
  return $d;
}

/* ---------- Plantillas de correo ---------- */
function default_templates() {
  return [
    ['id' => 't1', 'nombre' => 'Bienvenida tras descargar la guía', 'asunto' => 'Tu guía para invertir en Dubái', 'cuerpo' => "Hola {nombre},\n\nGracias por descargarte la guía. Espero que te ayude a ver con claridad cómo funciona la compra en Dubái.\n\nSi quieres, te dedico 20 minutos por videollamada para ver tu caso concreto: presupuesto, objetivo y qué zonas encajan contigo.\n\nUn abrazo,\nPascual Vidal\nTu inversión en Dubái"],
    ['id' => 't2', 'nombre' => 'Seguimiento tras la llamada', 'asunto' => 'Resumen de nuestra llamada', 'cuerpo' => "Hola {nombre},\n\nGracias por la llamada de hoy. Te resumo lo que hablamos y los siguientes pasos:\n\n· \n· \n\nCualquier duda, escríbeme por aquí o por WhatsApp.\n\nUn abrazo,\nPascual"],
    ['id' => 't3', 'nombre' => 'Envío de dossier', 'asunto' => 'Dossier de {proyecto}', 'cuerpo' => "Hola {nombre},\n\nTe adjunto el dossier de {proyecto} con planos, precios y plan de pagos.\n\nSi te encaja, te preparo una simulación de rentabilidad con números reales.\n\nUn abrazo,\nPascual"],
  ];
}

/* ---------- Google Calendar (dirección secreta iCal) ---------- */
function http_get($url) {
  if (function_exists('curl_init')) {
    $c = curl_init($url);
    curl_setopt_array($c, [CURLOPT_RETURNTRANSFER => true, CURLOPT_FOLLOWLOCATION => true, CURLOPT_MAXREDIRS => 3, CURLOPT_TIMEOUT => 12, CURLOPT_PROTOCOLS => CURLPROTO_HTTPS]);
    $body = curl_exec($c);
    $code = curl_getinfo($c, CURLINFO_HTTP_CODE);
    curl_close($c);
    return ($body !== false && $code < 400) ? $body : null;
  }
  $body = @file_get_contents($url, false, stream_context_create(['http' => ['timeout' => 12]]));
  return $body === false ? null : $body;
}

function ics_source($url) {
  $cache = store_read('icscache', []);
  if (($cache['url'] ?? '') === $url && time() - ($cache['t'] ?? 0) < 300) return $cache['body'];
  $body = http_get($url);
  if ($body === null || strpos($body, 'BEGIN:VCALENDAR') === false) return (($cache['url'] ?? '') === $url) ? ($cache['body'] ?? null) : null;
  store_write('icscache', ['url' => $url, 't' => time(), 'body' => $body]);
  return $body;
}

function ics_tz($name) {
  try { return new DateTimeZone($name ?: 'UTC'); } catch (Exception $e) { return new DateTimeZone('UTC'); }
}

// Devuelve [DateTime, allDay] o null.
function ics_time($val, $params, DateTimeZone $local) {
  if (preg_match('/^(\d{4})(\d{2})(\d{2})$/', $val, $m)) return [new DateTime("$m[1]-$m[2]-$m[3] 00:00:00", $local), true];
  if (preg_match('/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})(Z?)$/', $val, $m)) {
    $tz = $m[7] ? new DateTimeZone('UTC') : (isset($params['TZID']) ? ics_tz(trim($params['TZID'], '"')) : $local);
    return [new DateTime("$m[1]-$m[2]-$m[3] $m[4]:$m[5]:$m[6]", $tz), false];
  }
  return null;
}

function ics_text($s) { return str_replace(['\\n', '\\N', '\\,', '\;', '\\\\'], ["\n", "\n", ',', ';', '\\'], $s); }

// Expande una regla RRULE (DAILY/WEEKLY/MONTHLY/YEARLY con INTERVAL, COUNT, UNTIL, BYDAY, BYMONTHDAY).
function ics_occurrences(DateTime $start, $rule, $toTs) {
  $r = [];
  foreach (explode(';', $rule) as $p) { $kv = explode('=', $p, 2); if (count($kv) === 2) $r[strtoupper($kv[0])] = $kv[1]; }
  $freq = $r['FREQ'] ?? '';
  $int = max(1, (int) ($r['INTERVAL'] ?? 1));
  $count = isset($r['COUNT']) ? (int) $r['COUNT'] : 0;
  $until = null;
  if (!empty($r['UNTIL'])) { $u = ics_time($r['UNTIL'], [], new DateTimeZone('UTC')); if ($u) $until = $u[0]->getTimestamp() + ($u[1] ? 86399 : 0); }
  $days = ['MO' => 1, 'TU' => 2, 'WE' => 3, 'TH' => 4, 'FR' => 5, 'SA' => 6, 'SU' => 7];
  $byday = [];
  foreach (array_filter(explode(',', $r['BYDAY'] ?? '')) as $d) {
    if (preg_match('/^([+-]?\d+)?(MO|TU|WE|TH|FR|SA|SU)$/', $d, $m)) $byday[] = [(int) ($m[1] ?? 0), $days[$m[2]]];
  }
  $bymd = array_map('intval', array_filter(explode(',', $r['BYMONTHDAY'] ?? '')));
  $H = (int) $start->format('G'); $I = (int) $start->format('i'); $Sx = (int) $start->format('s');
  $out = []; $n = 0; $t0 = $start->getTimestamp();
  for ($p = 0; $p < 3000; $p++) {
    $cands = [];
    if ($freq === 'DAILY') {
      $d = clone $start; $d->modify('+' . ($p * $int) . ' day'); $cands[] = $d;
    } elseif ($freq === 'WEEKLY') {
      $wk = clone $start; $wk->modify('+' . ($p * $int) . ' week');
      $mon = clone $wk; $mon->modify('-' . ((int) $wk->format('N') - 1) . ' day');
      foreach ($byday ?: [[0, (int) $start->format('N')]] as $bd) { $d = clone $mon; $d->modify('+' . ($bd[1] - 1) . ' day'); $d->setTime($H, $I, $Sx); $cands[] = $d; }
    } elseif ($freq === 'MONTHLY' || $freq === 'YEARLY') {
      $base = clone $start; $base->modify('first day of this month');
      $base->modify('+' . ($p * $int * ($freq === 'YEARLY' ? 12 : 1)) . ' month');
      $y = (int) $base->format('Y'); $mo = (int) $base->format('n'); $dim = (int) $base->format('t');
      if ($byday) {
        foreach ($byday as $bd) {
          $hits = [];
          for ($dd = 1; $dd <= $dim; $dd++) { $x = clone $base; $x->setDate($y, $mo, $dd); if ((int) $x->format('N') === $bd[1]) $hits[] = $dd; }
          $sel = $bd[0] > 0 ? [$hits[$bd[0] - 1] ?? null] : ($bd[0] < 0 ? [$hits[count($hits) + $bd[0]] ?? null] : $hits);
          foreach (array_filter($sel) as $dd) { $x = clone $base; $x->setDate($y, $mo, $dd); $x->setTime($H, $I, $Sx); $cands[] = $x; }
        }
      } else {
        foreach ($bymd ?: [(int) $start->format('j')] as $dd) {
          if ($dd < 0) $dd = $dim + $dd + 1;
          if ($dd < 1 || $dd > $dim) continue;
          $x = clone $base; $x->setDate($y, $mo, $dd); $x->setTime($H, $I, $Sx); $cands[] = $x;
        }
      }
    } else {
      return [$start];
    }
    usort($cands, function ($a, $b) { return $a <=> $b; });
    foreach ($cands as $c) {
      $ts = $c->getTimestamp();
      if ($ts < $t0) continue;
      if ($until !== null && $ts > $until) return $out;
      if ($count && ++$n > $count) return $out;
      if ($ts > $toTs) return $out;
      $out[] = $c;
    }
  }
  return $out;
}

function ics_events($raw, $fromTs, $toTs, DateTimeZone $local) {
  $raw = preg_replace("/\r?\n[ \t]/", '', str_replace("\r\n", "\n", $raw));
  $events = []; $cur = null;
  foreach (explode("\n", $raw) as $line) {
    if ($line === 'BEGIN:VEVENT') { $cur = ['EXDATE' => []]; continue; }
    if ($line === 'END:VEVENT') { if ($cur) $events[] = $cur; $cur = null; continue; }
    if ($cur === null || !preg_match('/^([A-Z-]+)((?:;[^:]*)?):(.*)$/', $line, $m)) continue;
    $params = [];
    foreach (array_filter(explode(';', $m[2])) as $pp) { $kv = explode('=', $pp, 2); if (count($kv) === 2) $params[strtoupper($kv[0])] = $kv[1]; }
    if ($m[1] === 'EXDATE') { foreach (explode(',', $m[3]) as $x) $cur['EXDATE'][] = [$x, $params]; }
    elseif (!isset($cur[$m[1]])) $cur[$m[1]] = [$m[3], $params];
  }
  $overrides = []; $out = [];
  foreach ($events as $e) {
    if (isset($e['RECURRENCE-ID'])) { $t = ics_time($e['RECURRENCE-ID'][0], $e['RECURRENCE-ID'][1], $local); if ($t) $overrides[($e['UID'][0] ?? '') . '|' . $t[0]->getTimestamp()] = 1; }
  }
  foreach ($events as $e) {
    if (!isset($e['DTSTART']) || strtoupper($e['STATUS'][0] ?? '') === 'CANCELLED') continue;
    $s = ics_time($e['DTSTART'][0], $e['DTSTART'][1], $local);
    if (!$s) continue;
    [$start, $allDay] = $s;
    $end = isset($e['DTEND']) ? ics_time($e['DTEND'][0], $e['DTEND'][1], $local) : null;
    $dur = $end ? max(0, $end[0]->getTimestamp() - $start->getTimestamp()) : ($allDay ? 86400 : 3600);
    $uid = $e['UID'][0] ?? '';
    $ex = [];
    foreach ($e['EXDATE'] as $x) { $t = ics_time($x[0], $x[1], $local); if ($t) $ex[$t[0]->getTimestamp()] = 1; }
    $list = (isset($e['RRULE']) && !isset($e['RECURRENCE-ID'])) ? ics_occurrences($start, $e['RRULE'][0], $toTs) : [$start];
    foreach ($list as $o) {
      $ts = $o->getTimestamp();
      if ($ts + $dur < $fromTs || $ts > $toTs || isset($ex[$ts])) continue;
      if (isset($e['RRULE']) && !isset($e['RECURRENCE-ID']) && isset($overrides["$uid|$ts"])) continue;
      $endTs = $ts + $dur;
      $out[] = [
        'id' => substr(md5($uid . $ts), 0, 12),
        'titulo' => cut(ics_text($e['SUMMARY'][0] ?? '(Sin título)'), 200),
        'inicio' => $allDay ? $o->format('Y-m-d') : $o->format('c'),
        'fin' => $allDay ? (new DateTime('@' . ($endTs - 1)))->setTimezone($local)->format('Y-m-d') : date('c', $endTs),
        'todoElDia' => $allDay,
        'lugar' => cut(ics_text($e['LOCATION'][0] ?? ''), 200),
        'nota' => cut(ics_text($e['DESCRIPTION'][0] ?? ''), 600),
      ];
    }
  }
  usort($out, function ($a, $b) { return strcmp($a['inicio'], $b['inicio']); });
  return $out;
}
