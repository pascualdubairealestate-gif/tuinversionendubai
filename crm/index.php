<?php
/* CRM · Tu inversión en Dubái — acceso y panel */
require __DIR__ . '/lib.php';
header('X-Robots-Tag: noindex, nofollow');
header('Cache-Control: no-store');
header('X-Frame-Options: DENY');

$error = '';
$view = !is_setup() ? 'setup' : (authed() ? 'app' : 'login');

if (($_SERVER['REQUEST_METHOD'] ?? '') === 'POST') {
  $form = $_POST['form'] ?? '';
  if ($form === 'logout') {
    crm_session();
    $_SESSION = [];
    session_destroy();
    header('Location: ' . crm_base());
    exit;
  }
  if ($form === 'setup' && $view === 'setup') {
    $key = strtoupper(trim((string) ($_POST['clave'] ?? '')));
    $pass = (string) ($_POST['password'] ?? '');
    if (!rate('setup', 10, 900, false)) $error = 'Demasiados intentos. Espera 15 minutos.';
    elseif (!hash_equals(SETUP_KEY_HASH, hash('sha256', $key))) { rate('setup', 10, 900); $error = 'La clave de instalación no es correcta.'; }
    elseif (strlen($pass) < 10) $error = 'La contraseña necesita al menos 10 caracteres.';
    elseif ($pass !== ($_POST['password2'] ?? '')) $error = 'Las contraseñas no coinciden.';
    else {
      with_lock('config', function () use ($pass) {
        $cfg = config();
        if (empty($cfg['hash'])) {
          $cfg['hash'] = password_hash($pass, PASSWORD_DEFAULT);
          $cfg['v'] = bin2hex(random_bytes(8));
          store_write('config', $cfg);
        }
      });
      login_session();
      header('Location: ' . crm_base());
      exit;
    }
  }
  if ($form === 'login' && $view === 'login') {
    if (!rate('login', 8, 900, false)) $error = 'Demasiados intentos. Espera 15 minutos.';
    elseif (password_verify((string) ($_POST['password'] ?? ''), config()['hash'])) {
      login_session();
      header('Location: ' . crm_base());
      exit;
    } else { rate('login', 8, 900); $error = 'Contraseña incorrecta.'; }
  }
}
$v = '20261029b';
?><!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <meta name="robots" content="noindex, nofollow" />
  <meta name="theme-color" content="#ffffff" />
  <title>CRM · Tu inversión en Dubái</title>
  <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23070d18'/%3E%3Ctext x='32' y='42' font-family='Georgia,serif' font-size='28' fill='%23f7931e' text-anchor='middle'%3EPV%3C/text%3E%3C/svg%3E" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,600&family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="app.css?v=<?= $v ?>" />
</head>
<body>
<?php if ($view !== 'app'): ?>
  <main class="auth">
    <form class="auth-card" method="post" autocomplete="on">
      <div class="brand"><span class="logo">PV</span><span>CRM <em>Tu inversión en Dubái</em></span></div>
      <?php if ($view === 'setup'): ?>
        <h1>Activa tu CRM</h1>
        <p class="muted">Introduce la clave de instalación que te di y elige tu contraseña. Solo se hace una vez.</p>
        <input type="hidden" name="form" value="setup" />
        <label>Clave de instalación<input name="clave" required autocomplete="off" placeholder="XXXXXX-XXXXXX-XXXXXX-XXXXXX" /></label>
        <label>Nueva contraseña<input type="password" name="password" required minlength="10" autocomplete="new-password" /></label>
        <label>Repite la contraseña<input type="password" name="password2" required minlength="10" autocomplete="new-password" /></label>
        <button class="btn primary" type="submit">Activar</button>
      <?php else: ?>
        <h1>Entrar</h1>
        <input type="hidden" name="form" value="login" />
        <input type="text" name="username" value="pascual" autocomplete="username" hidden />
        <label>Contraseña<input type="password" name="password" required autofocus autocomplete="current-password" /></label>
        <button class="btn primary" type="submit">Entrar</button>
      <?php endif; ?>
      <?php if ($error): ?><p class="err"><?= h($error) ?></p><?php endif; ?>
    </form>
  </main>
<?php else: ?>
  <div class="shell">
    <aside class="side">
      <div class="brand"><span class="logo">PV</span><span>CRM <em>Tu inversión en Dubái</em></span></div>
      <nav class="nav" aria-label="Secciones">
        <a href="#inicio" class="nav-link" data-nav="inicio"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M10 21v-6h4v6"/></svg><span>Inicio</span></a>
        <a href="#contactos" class="nav-link" data-nav="contactos"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="9" cy="8" r="3.5"/><path d="M2.5 20c.8-3.6 3.4-5.5 6.5-5.5s5.7 1.9 6.5 5.5"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7"/><path d="M18 14.7c1.8.7 3 2.5 3.5 5.3"/></svg><span>Contactos</span></a>
        <a href="#ventas" class="nav-link" data-nav="ventas"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="5" height="16" rx="1.5"/><rect x="10" y="4" width="5" height="11" rx="1.5"/><rect x="17" y="4" width="4" height="7" rx="1.5"/></svg><span>Ventas</span></a>
        <a href="#correo" class="nav-link" data-nav="correo"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 6.5 8.5 6.5 8.5-6.5"/></svg><span>Correo</span></a>
        <a href="#calendario" class="nav-link" data-nav="calendario"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg><span>Calendario</span></a>
        <a href="#documentos" class="nav-link" data-nav="documentos"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/></svg><span>Documentos</span></a>
      </nav>
      <div class="side-foot">
        <button class="nav-link" data-act="settings"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1 7 17M17 7l2.1-2.1"/></svg><span>Ajustes</span></button>
        <form method="post"><input type="hidden" name="form" value="logout" /><button class="nav-link" type="submit"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 16l-4-4 4-4M6 12h10"/></svg><span>Salir</span></button></form>
      </div>
    </aside>
    <div class="content">
      <header class="top">
        <h1 id="page-title">Inicio</h1>
        <div class="top-actions">
          <button class="btn icon mob-only" data-act="settings" aria-label="Ajustes"><svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M2 12h3M19 12h3M4.9 19.1 7 17M17 7l2.1-2.1"/></svg></button>
          <button class="btn primary" data-act="new">+ Nuevo contacto</button>
        </div>
      </header>
      <main id="main"></main>
    </div>
  </div>

  <aside class="drawer" id="drawer" hidden>
    <div class="drawer-bg" data-close></div>
    <div class="drawer-panel" role="dialog" aria-modal="true" aria-labelledby="d-title"></div>
  </aside>
  <div class="toast" id="toast" role="status" aria-live="polite"></div>
  <script src="app.js?v=<?= $v ?>"></script>
<?php endif; ?>
</body>
</html>
