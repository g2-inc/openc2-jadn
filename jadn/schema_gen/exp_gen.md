<!-- Generated from schema/exp.jadn, Fri Nov 16 10:38:31 2018-->
## Schema
.   | .  
---: | :---
title: | Experimental Schema Features
module: | oasis-open.org/openc2/oc2ls/v1.0/experimental
description: | Profile used to test schema features not used in existing language or profiles
exports: | Target, Specifiers, Args, Results
imports: | 
patch: | 0

##3.2 Structure Types
###3.2.1 Target

New targets

**Target (Choice)**

ID | Name | Type | Description
---: | :--- | :--- | :---
1 | hashes | Hashes | Hash values serialized as hex
2 | ipv4_addr_s | IPv4-String | IPv4 address as type-specific string (dotted-decimal): '192.168.0.254'
3 | ipv4_addr_x | IPv4-Hex | IPv4 address serialized as hex: 'C0A800FE'
4 | ipv4_addr_b64 | IPv4-Base64url | IPv4 address serialized as Base64-url: 'wKgA_g'
5 | ipv6_addr_s | IPv6-String | IPv6 address as type-specific string (colon-hex): ''
6 | ipv6_addr_x | IPv6-Hex | IPv6 address serialized as hex: ''
7 | ipv6_addr_b64 | IPv6-Base64url | IPv6 address serialized as Base64-url: ''

###3.2.2 Hashes
Cryptographic Hash values

**Hashes (Map)**

ID | Name | Type | # | Description
---: | :--- | :--- | ---: | :---
1 | md5 | Bin-128 | 0..1 | MD5 hash as defined in RFC3121
4 | sha1 | Bin-160 | 0..1 | SHA1 hash as defined in RFC3174
6 | sha256 | Bin-256 | 0..1 | SHA256 as defined in RFC6234

###3.2.3 Args
Experimental command arguments

**Args (Map)**

ID | Name | Type | # | Description
---: | :--- | :--- | ---: | :---


###3.2.4 Specifiers
Experimental actuator specifiers

**Specifiers (Map)**

ID | Name | Type | # | Description
---: | :--- | :--- | ---: | :---


###3.2.5 Results
Experimental results

**Results (Map)**

ID | Name | Type | # | Description
---: | :--- | :--- | ---: | :---
1 | knps | KNP | 0..n | Generic set of key:number pairs.
42 | battery | Battery-Properties | 0..1 | Set of properties defined for an energy storage device

###3.2.6 KNP

**KNP (Array)**

ID | Type | # | Description
---: | :--- | ---: | :---
1 | String | 1 | "key": name of this item
2 | Number | 1 | "value": numeric value of this item

###3.2.7 Battery-Properties

**Battery-Properties (Map)**

ID | Name | Type | # | Description
---: | :--- | :--- | ---: | :---
7 | voltage | Integer | 0..1 | Battery output voltage (millivolts)
18 | charge | Percentage | 0..1 | State of charge (percent)
26 | manufacturer | String | 0..1 | Product name for this device

##3.3 Primitive Types

Name | Type | Description
:--- | :--- | :---
Bin-128 | Binary.x | 128 bit value, hex display
Bin-160 | Binary.x | 160 bit value, hex display
Bin-256 | Binary.x | 256 bit value, hex display
IPv4-Hex | Binary | Value must be 32 bits [4..4].  Value displayed in hex (Binary.x)
IPv4-Base64url | Binary (ipv4) | Value must be 32 bits (ipv4).  Value displayed in base64url (Binary) default
IPv4-String | Binary (ipv4) | Value must be 32 bits (ipv4).  Value displayed in ipv4 dotted-decimal (Binary.s:ipv4)
IPv6-Hex | Binary (ipv6) | Value must be 128 bits (ipv6).  Value displayed in hex (Binary.x)
IPv6-Base64url | Binary | Value must be 128 bits [16..16].  Value displayed in base64url (Binary) default
IPv6-String | Binary | Value must be 128 bits [16..16].  Value displayed in ipv6 colon-hex (Binary.s:ipv6)
Percentage | Number | Real number in the range 0.0-100.0

