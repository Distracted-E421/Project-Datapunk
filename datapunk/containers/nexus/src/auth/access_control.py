from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum
import ipaddress
import geoip2.database
import geoip2.errors
import re

class AccessRuleType(Enum):
    ALLOW = "allow"
    DENY = "deny"

@dataclass
class GeoRule:
    countries: Set[str]
    regions: Set[str] = field(default_factory=set)
    cities: Set[str] = field(default_factory=set)
    rule_type: AccessRuleType = AccessRuleType.ALLOW

@dataclass
class IPRule:
    networks: Set[str]  # CIDR notation
    rule_type: AccessRuleType = AccessRuleType.ALLOW
    description: str = ""

@dataclass
class LocationInfo:
    country_code: str
    country_name: str
    region: str
    city: str
    latitude: float
    longitude: float

class AccessControl:
    def __init__(self, geoip_db_path: str, default_allow: bool = False):
        """Initialize with GeoIP database and default policy."""
        self.geoip_reader = geoip2.database.Reader(geoip_db_path)
        self.default_allow = default_allow
        
        self._ip_rules: List[IPRule] = []
        self._geo_rules: List[GeoRule] = []
        self._ip_networks = {}  # Cache for parsed networks
        
    def add_ip_rule(self, networks: Set[str], rule_type: AccessRuleType, description: str = ""):
        """Add an IP-based access rule."""
        # Validate CIDR notation
        parsed_networks = set()
        for network in networks:
            try:
                parsed_networks.add(str(ipaddress.ip_network(network)))
            except ValueError as e:
                raise ValueError(f"Invalid network {network}: {str(e)}")
                
        rule = IPRule(networks=parsed_networks, rule_type=rule_type, description=description)
        self._ip_rules.append(rule)
        
        # Update network cache
        for network in parsed_networks:
            self._ip_networks[network] = ipaddress.ip_network(network)
            
    def add_geo_rule(self, countries: Set[str], regions: Set[str] = None,
                     cities: Set[str] = None, rule_type: AccessRuleType = AccessRuleType.ALLOW):
        """Add a geography-based access rule."""
        rule = GeoRule(
            countries=set(c.upper() for c in countries),
            regions=set(regions or []),
            cities=set(cities or []),
            rule_type=rule_type
        )
        self._geo_rules.append(rule)
        
    def get_location_info(self, ip_address: str) -> Optional[LocationInfo]:
        """Get location information for an IP address."""
        try:
            response = self.geoip_reader.city(ip_address)
            return LocationInfo(
                country_code=response.country.iso_code,
                country_name=response.country.name,
                region=response.subdivisions.most_specific.name if response.subdivisions else "",
                city=response.city.name if response.city else "",
                latitude=response.location.latitude,
                longitude=response.location.longitude
            )
        except (geoip2.errors.AddressNotFoundError, ValueError):
            return None
            
    def check_ip_rules(self, ip_address: str) -> tuple[bool, Optional[str]]:
        """Check if IP address matches any rules."""
        try:
            ip = ipaddress.ip_address(ip_address)
        except ValueError:
            return False, f"Invalid IP address: {ip_address}"
            
        # Check each rule in order
        for rule in self._ip_rules:
            for network_str in rule.networks:
                network = self._ip_networks[network_str]
                if ip in network:
                    return (
                        rule.rule_type == AccessRuleType.ALLOW,
                        f"IP {ip_address} matched {rule.rule_type.value} rule: {rule.description}"
                    )
                    
        return self.default_allow, "No IP rules matched, using default policy"
        
    def check_geo_rules(self, location: LocationInfo) -> tuple[bool, Optional[str]]:
        """Check if location matches any geographic rules."""
        if not location:
            return self.default_allow, "No location information available"
            
        # Check each rule in order
        for rule in self._geo_rules:
            country_match = location.country_code in rule.countries
            region_match = not rule.regions or location.region in rule.regions
            city_match = not rule.cities or location.city in rule.cities
            
            if country_match and region_match and city_match:
                return (
                    rule.rule_type == AccessRuleType.ALLOW,
                    f"Location matched {rule.rule_type.value} rule: "
                    f"{location.country_code}/{location.region}/{location.city}"
                )
                
        return self.default_allow, "No geographic rules matched, using default policy"
        
    def check_access(self, ip_address: str) -> tuple[bool, str]:
        """Check if access should be allowed for an IP address."""
        # First check IP rules
        ip_allowed, ip_reason = self.check_ip_rules(ip_address)
        if not self.default_allow and ip_allowed:
            return True, ip_reason
        if self.default_allow and not ip_allowed:
            return False, ip_reason
            
        # Then check geographic rules
        location = self.get_location_info(ip_address)
        if location:
            geo_allowed, geo_reason = self.check_geo_rules(location)
            return geo_allowed, geo_reason
            
        return self.default_allow, "No rules matched and no location info available"
        
    def is_ip_in_range(self, ip_address: str, latitude: float, longitude: float,
                       radius_km: float) -> bool:
        """Check if IP is within a geographic radius."""
        location = self.get_location_info(ip_address)
        if not location:
            return False
            
        # Calculate distance using Haversine formula
        from math import radians, sin, cos, sqrt, atan2
        
        lat1, lon1 = radians(latitude), radians(longitude)
        lat2, lon2 = radians(location.latitude), radians(location.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = 6371 * c  # Earth's radius in km
        
        return distance <= radius_km 