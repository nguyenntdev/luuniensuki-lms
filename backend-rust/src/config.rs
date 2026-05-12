use std::net::{IpAddr, Ipv4Addr, SocketAddr};

#[derive(Clone, Debug)]
pub struct Settings {
    pub bind_addr: SocketAddr,
    pub app_name: String,
    pub legacy_api_addr: SocketAddr,
}

impl Settings {
    pub fn from_env() -> Self {
        let host = std::env::var("API_HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
        let port = std::env::var("API_PORT")
            .ok()
            .and_then(|value| value.parse::<u16>().ok())
            .unwrap_or(8001);
        let ip = host
            .parse::<IpAddr>()
            .unwrap_or(IpAddr::V4(Ipv4Addr::UNSPECIFIED));
        let legacy_host = std::env::var("LEGACY_API_HOST").unwrap_or_else(|_| "api".to_string());
        let legacy_port = std::env::var("LEGACY_API_PORT")
            .ok()
            .and_then(|value| value.parse::<u16>().ok())
            .unwrap_or(8000);
        let legacy_ip = resolve_host(&legacy_host).unwrap_or(IpAddr::V4(Ipv4Addr::LOCALHOST));

        Self {
            bind_addr: SocketAddr::new(ip, port),
            app_name: "luuniensuki-api-rust".to_string(),
            legacy_api_addr: SocketAddr::new(legacy_ip, legacy_port),
        }
    }
}

fn resolve_host(host: &str) -> Option<IpAddr> {
    host.parse::<IpAddr>().ok().or_else(|| {
        std::net::ToSocketAddrs::to_socket_addrs(&(host, 0))
            .ok()
            .and_then(|mut addrs| addrs.next())
            .map(|addr| addr.ip())
    })
}
