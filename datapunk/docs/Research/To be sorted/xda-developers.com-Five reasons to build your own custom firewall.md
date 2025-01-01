Five reasons to build your own custom firewall

xda-developers.com/reasons-build-custom-firewall

December 25, 2024

Adding a custom firewall and router to your network can be one of the biggest upgrades you
can make, skipping the limitations of normal ISP boxes or even more expensive proprietary
routers and handing you back complete control, customization, and flexibility in your network.
They offer a vast range of features, from simple tweaks to enterprise-grade integrations or
high-availability setups that are far outside most people's requirements.

So whether you're a seasoned homelabber looking to take the next step, or just a curious
home user sick of your ISP router, here are some of the reasons that we think building a
custom firewall/router combo is a great upgrade for everyone's network.

5 A custom firewall can enhance your security

Fine tune rules for your needs

1/6

One of the best reasons to run a custom firewall is to fine tune your network's security
posture. This can be everything from opening up specific IP ranges for game servers or
services at home, to blocking entire countries with more advanced network filtering. Most
custom firewalls also support some form of automatic intrusion protection and detection
system (known as IDS/IPS). These tools can monitor your network activity proactively,
flagging and then blocking or restricting any traffic that is flagged as unusual, out of pattern
or potentially concerning. The sensitivity of these tools can also be tweaked, with specific
rulesets (or even custom rules) available to add, and while not foolproof, can potentially stop
a would-be attacker in their tracks if another device on your network is compromised.

These tools can also help identify other concerning network trends. For example, if a large
amount of data was being transferred over your network overnight which could indicate the
presence of some malware, or if a specific smart home device was communicating
constantly with servers in a region of the world you may not trust with your data.

In theory, you can separate your firewall and router, but this isn't super applicable to most
places outside an enterprise environment. Hence, we'll be talking about a firewall/router
combo, with a focus on the benefits of firewalls.

4 Take your networking to the next level

Upgrade your network and learn something along the way

2/6

As we've covered before, setting up a custom firewall and router combo can take your
networking game to the next level by introducing all kinds of enterprise grade features at a
fraction of the cost. This can be anything from setting up custom VLANs, VPNs, load
balancing or even high-availability setups.

Tools like pfSense are relatively easy to get started with, well documented, and can take your
networking game up a significant notch without needing any specialist knowledge or deep
customization to get going. There are a lot of possibilities here, and experimenting with your
network and router is a great way to learn about practical networking concepts — which (in
my mind) are far easier to grasp than reading endless Wikipedia pages on networking
standards or posts on how to configure something specific.

Virtualizing a router isn't anywhere nearly as difficult as you might
think, provided you've got some spare network interfaces

7

3 Integrate with your home lab

Unlock a world of power and potential for your lab

3/6

If you're a homelabber, having a custom firewall and router is basically a must. Not only does
it open up a world of other integrations (for example, expanding your logging and
monitoring), but it makes things like opening ports, setting up a DMZ for your services,
custom routing, or static IPs and even subnetting or VLANs for your devices a lot easier.
Custom routers put control in your hands, and while this can be dangerous (especially if
you're exposing devices to the wider internet), it also opens up a world of possibilities. Ever
wanted to set a failover WAN connection for when your ISP decides it's just not their day? Or
configure alerting and monitoring for when your internet speed dips below a certain point? A
sandboxed environment for testing a new honeypot, or placing a device in a DMZ for
segregated public access?

The world is your oyster when it comes to combining your home lab and router, as they
effectively form two halves of the same coin (i.e., by providing your internal services). A
custom router can also integrate more easily with other self-hosted services, like a DHCP or
DNS server.

Personally, I think one of the better home lab and firewall projects to embark on is setting up
a Grafana-based dashboard for your router, integrating data on your network, regular
download or speed tests, and IDS/IDP information from the likes of Snort.

2 Custom routers don't need to be expensive

A cheap and cheerful custom router is perfectly possible

4/6

Building a custom router with the likes of pfSense doesn't need to break the bank, and
there's no need to go out and buy expensive, prebuilt hardware to do it. As we've covered
before on XDA, building a custom router can be relatively straightforward, and the hardware
requirements are rock bottom (especially if you're not pushing your network too hard with
many people or clients.) If you've got an existing home lab with Proxmox or another
hypervisor, you can also virtualize your router and firewall, provided that you've got a
hypervisor node with at least two free network interfaces.

1 Logging and monitoring

See deeper into your network than ever before

5/6

A final good argument for a custom firewall that we touched on earlier is that it allows you to
integrate your own custom logging and monitoring stack. It is great not only to learn
something about setting this kind of thing up, but also to get some new insights into your
network. This can be anything from running regular speed tests to ensure your ISP is
providing the speed you're paying for, to identifying misbehaving devices which may have
been compromised by malware or Internet of things and smart home devices that are
communicating with locations on the internet you might not need.

Most custom router firmware comes with a host of integrations for everything from
Prometheus to syslog, and if it's not natively available, there are integrations and plugins that
can be easily installed.

A custom firewall is a great upgrade to your network

Installing a custom firewall for your network is not only a good way to learn something about
networking and network security in general, it's also the perfect opportunity to take back
control. ISP routers are useful for most people, and are configured in a way that's sensible
and secure (mostly...), but by installing your own router and firewall combo, you can really
deep dive into the traffic that's moving through your network and the security protection
around it.

6/6

