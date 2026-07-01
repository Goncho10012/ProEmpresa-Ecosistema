import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate, Link, useNavigate } from 'react-router-dom';
import { LogOut, Users, ClipboardList, Briefcase, Activity, BarChart3 } from 'lucide-react';
import api, { setSession, logout, isAuth, user } from './services/api.js';
import logo from './assets/logo_proempresa.png';
import './styles.css';

function Login() {
  const nav = useNavigate();
  const [username, setUsername] = React.useState('admin');
  const [password, setPassword] = React.useState('admin123');
  const [error, setError] = React.useState('');
  const [loading, setLoading] = React.useState(false);

  async function submit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const usuario = String(username || '').trim();
      const response = await api.post('/auth/login', {
        username: usuario,
        codigo_empleado: usuario,
        password: String(password || ''),
      });

      setSession(response.data);
      nav('/', { replace: true });
    } catch (err) {
      setError('No se pudo iniciar sesión. Verifique sus credenciales o la conexión con el Core.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <form className="login-card" onSubmit={submit}>
        <img src={logo} alt="Financiera ProEmpresa" />
        <h1>Acceso al Portal Interno</h1>
        <p>Gestión operativa de clientes, cartera, créditos, solicitudes y operaciones.</p>

        <label>Usuario institucional</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} />

        <label>Contraseña</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />

        {error && <div className="error">{error}</div>}

        <button disabled={loading}>{loading ? 'Ingresando...' : 'Ingresar al sistema'}</button>
      </form>
    </main>
  );
}

function Layout({ children }) {
  const currentUser = user();

  return (
    <div className="app">
      <aside>
        <img src={logo} alt="Financiera ProEmpresa" />
        <p>Portal Interno</p>
        <Link to="/"><Activity />Inicio</Link>
        <Link to="/clientes"><Users />Clientes</Link>
        <Link to="/cartera"><Briefcase />Cartera</Link>
        <Link to="/solicitudes"><ClipboardList />Solicitudes</Link>
        <Link to="/operaciones"><BarChart3 />Operaciones</Link>
        <button onClick={logout}><LogOut />Salir</button>
      </aside>
      <section className="content">
        <header>
          <b>Core Operativo ProEmpresa</b>
          <span>{currentUser?.username || 'usuario'} · {currentUser?.rol || 'sesión activa'}</span>
        </header>
        {children}
      </section>
    </div>
  );
}

function Private({ children }) {
  if (!isAuth()) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
}

function ErrorBox({ message }) {
  return <div className="error table-error">{message}</div>;
}

function Dashboard() {
  const [data, setData] = React.useState(null);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (!isAuth()) return undefined;

    let active = true;
    api.get('/reportes/dashboard')
      .then((response) => {
        if (active) setData(response.data);
      })
      .catch(() => {
        if (active) setError('No se pudo cargar el dashboard.');
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <Private>
      <h1>Inicio</h1>
      {error && <ErrorBox message={error} />}
      <div className="cards">
        {['clientes', 'solicitudes', 'cartera_pendiente', 'operaciones', 'monto_solicitado'].map((key) => (
          <div className="card" key={key}>
            <span>{key.replaceAll('_', ' ')}</span>
            <b>{data?.[key] ?? '...'}</b>
          </div>
        ))}
      </div>
    </Private>
  );
}

function Clientes() {
  const [data, setData] = React.useState([]);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (!isAuth()) return undefined;

    let active = true;
    api.get('/clientes')
      .then((response) => {
        if (active) setData(response.data);
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar los clientes.');
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <Private>
      <h1>Clientes</h1>
      {error && <ErrorBox message={error} />}
      <Table
        heads={['Documento', 'Cliente', 'Teléfono', 'Negocio', 'Dirección negocio']}
        rows={data.map((x) => [x.numero_documento, `${x.nombres} ${x.apellidos}`, x.telefono, x.nombre_negocio, x.direccion_negocio])}
      />
    </Private>
  );
}

function Cartera() {
  const [data, setData] = React.useState([]);
  const [error, setError] = React.useState('');

  const load = React.useCallback(async () => {
    try {
      setError('');
      const response = await api.get('/cartera');
      setData(response.data);
    } catch {
      setError('No se pudo cargar la cartera comercial.');
    }
  }, []);

  React.useEffect(() => {
    if (!isAuth()) return undefined;
    load();
    return undefined;
  }, [load]);

  return (
    <Private>
      <h1>Cartera comercial</h1>
      {error && <ErrorBox message={error} />}
      <Table
        heads={['Cliente', 'Solicitud', 'Monto', 'Prioridad', 'Estado visita', 'Estado solicitud']}
        rows={data.map((x) => [
          `${x.nombres} ${x.apellidos}`,
          x.numero_expediente,
          'S/ ' + Number(x.monto_solicitado || 0).toFixed(2),
          x.prioridad,
          x.estado_visita,
          x.estado_solicitud,
        ])}
      />
    </Private>
  );
}

function Solicitudes() {
  const [data, setData] = React.useState([]);
  const [error, setError] = React.useState('');

  const load = React.useCallback(async () => {
    try {
      setError('');
      const response = await api.get('/solicitudes');
      setData(response.data);
    } catch {
      setError('No se pudieron cargar las solicitudes.');
    }
  }, []);

  React.useEffect(() => {
    if (!isAuth()) return undefined;
    load();
    return undefined;
  }, [load]);

  async function aprobar(id, monto) {
    try {
      await api.patch(`/solicitudes/${id}/estado`, {
        estado: 'aprobada',
        monto_aprobado: monto,
        comentario: 'Aprobado desde portal',
      });
      await load();
    } catch {
      setError('No se pudo aprobar y desembolsar la solicitud.');
    }
  }

  async function rechazar(id) {
    try {
      await api.patch(`/solicitudes/${id}/estado`, {
        estado: 'rechazada',
        motivo_rechazo: 'No cumple política',
        comentario: 'Rechazado desde portal',
      });
      await load();
    } catch {
      setError('No se pudo rechazar la solicitud.');
    }
  }

  return (
    <Private>
      <h1>Solicitudes</h1>
      {error && <ErrorBox message={error} />}
      <table>
        <thead>
          <tr>{['Expediente', 'Cliente', 'Monto', 'Plazo', 'Estado', 'Acción'].map((h) => <th key={h}>{h}</th>)}</tr>
        </thead>
        <tbody>
          {data.map((x) => (
            <tr key={x.id}>
              <td>{x.numero_expediente}</td>
              <td>{x.nombres} {x.apellidos}</td>
              <td>S/ {Number(x.monto_solicitado || 0).toFixed(2)}</td>
              <td>{x.plazo_meses} meses</td>
              <td><span className="badge">{x.estado}</span></td>
              <td>
                <button className="small" onClick={() => aprobar(x.id, x.monto_solicitado)}>Aprobar y desembolsar</button>
                <button className="ghost" onClick={() => rechazar(x.id)}>Rechazar</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Private>
  );
}

function Operaciones() {
  const [data, setData] = React.useState([]);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (!isAuth()) return undefined;

    let active = true;
    api.get('/operaciones')
      .then((response) => {
        if (active) setData(response.data);
      })
      .catch(() => {
        if (active) setError('No se pudieron cargar las operaciones.');
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <Private>
      <h1>Operaciones</h1>
      {error && <ErrorBox message={error} />}
      <Table
        heads={['Código', 'Cliente', 'Tipo', 'Monto', 'Estado', 'Fecha']}
        rows={data.map((x) => [
          x.codigo_operacion,
          x.cliente_nombre,
          x.tipo_operacion,
          'S/ ' + Number(x.monto || 0).toFixed(2),
          x.estado,
          x.created_at ? new Date(x.created_at).toLocaleString('es-PE') : '-',
        ])}
      />
    </Private>
  );
}

function Table({ heads, rows }) {
  return (
    <table>
      <thead>
        <tr>{heads.map((h) => <th key={h}>{h}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>{r.map((c, j) => <td key={j}>{c || '-'}</td>)}</tr>
        ))}
      </tbody>
    </table>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Dashboard />} />
        <Route path="/clientes" element={<Clientes />} />
        <Route path="/cartera" element={<Cartera />} />
        <Route path="/solicitudes" element={<Solicitudes />} />
        <Route path="/operaciones" element={<Operaciones />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
