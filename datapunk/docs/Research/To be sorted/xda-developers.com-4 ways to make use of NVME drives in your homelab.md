4 ways to make use of NVME drives in your homelab

xda-developers.com/ways-make-use-nvme-drives-homelab

If you're regularly upgrading your PC, or swapping parts in and out of machines like me, you
might find you end up with quite a few spare drives lying around. Certainly, I've got a small
pile of older, smaller, 2.5" SATA SSDs lying around that are no longer in use, but as the world
increasingly switches to NVMe (and motherboards still insist on retaining only one M.2 slot..)
it's easy to end up with several spare drives looking for a new home.

Adding a few higher-performance drives can be great for your homelab, not only for a quick
performance bump, but also as a good learning exercise. Optimizing filesystems and storage
performance is (in my humble opinion) one of the more finicky tasks homelabbers have to
deal with, and understanding filesystems themselves can really help with that. With that in
mind, here are a few ideas on how you could integrate a spare NVMe drive or two into your
homelab, and maybe learn a thing or two along the way.

4 Supercharge your VM's performance

Dedicate an NVME drive to your most storage-hungry VMs

One easy application of a spare NVMe drive is as a dedicated storage drive for your most
performance hungry VMs. This might be anything from a NAS instance, seedbox or caching
server (though it would probably be overkill for all of those). Adding superspeed storage

1/5

could help a graphical VM like a Windows instance feel more responsive when running in a
virtualized environment.

Now, while for a lot of people's workload, a dedicated drive might be overkill (though I'm at
pains never to underestimate the crazy things people might be runnning in their labs), it's
always possible to dedicate a drive to multiple, higher performance loads. This might involve
having all your core NAS services running on a single drive, or running 2-3 more burstable,
high power VMs on the same drive to give them temporary access to its full performance as
required.

Setting up a dedicated drive in a hypervisor like Proxmox is relatively easy; you'll need to
wipe your drive, initialize your drive with a partition table like GPT, and then setup an LVM, all
of which can be done within the Proxmox UI. It's then simple to store container or virtual
machines on that drive, and Proxmox even makes migrating them from one drive to another
relatively simple.

3 Dedicate a flash read cache for your NAS

Configure your disk as an L2Arc cache

Another more application level use of your NVMe SSD is as an L2ARC cache for your ZFS
devices like your NAS. ZFS stores frequently used data in a system of tiered read caches.

ZFS's primary cache is known as ARC (or Adaptive Replacement Cache), which typically
resides in RAM. This is typically a smaller cache for the most essential and frequently used
data, and is a big reason why it's often recommended to ensure plenty of RAM is available to
ZFS. The second tier of read caching is known as L2ARC (i.e. level 2 ARC). This cache
typically resides on disk, is much larger, and stores the next set of most frequently accessed
data. It's this tier of caching that you can take advantage of a spare NVMe drive for, adding a
significantly sized and very high-performance cache.

You might want to think about what you're using your NAS here for before configuring this.
For example, if you're only using your NAS for TV shows and movies, where you're unlikely
to need very fast repeat access to data, you may only see marginal performance gains. If
you're using your NAS (or any other ZFS based system) for more repeatable data, like

2/5

document storage, video or photo editing, programming, etc, you may see significant
performance gains. It's up to you to decide what percentage of your drive might be best used
as pure, fast storage and what size might be best used for a caching layer.

2 Set up a ZIL/SLOG for ZFS

If you've decided a read cache in ZFS isn't going to add a lot of value, you could always
configure a write cache (not technically a write cache) with ZIL/SLOG. This can get a bit
tricky, but the gist here is that by adding a separate high-speed logging device for the ZFS
Intent Log (or ZIL), synchronous transactions can be safely performed with far higher
performance. The ZIL is a location on disk where data is temporarily held before its location
is finalized. ZFS stores the ZIL on disk in your storage pool, and this needs to be updated
both before and after a write to disk occurs, adding significant latency and performance
overhead — especially for a lot of small, random writes.

Now this is only true for synchronous writes in ZFS, which require special conditions to be
met before this is used (as for most user applications, asynchronous mode is much faster
and can survive a lower standard of data integrity). We'd only really recommend this if you're
running a networked-disk workload like NFS, or a database like Postgres directly on top of
your ZFS pool.

3/5

We've skipped a lot of detail for brevity here — ZFS can be a big topic. There's a great wiki
page on the TrueNAS wiki about when to use synchronous writes and a ZIL/SLOG, as well
as some deeper explanation on ZFS caching more generally at 45drives.

1 Setup a pure NVMe cluster for ultra-fast applications

Jump into the world of containers with your own cluster

Source: Raspberry Pi Foundation
Now this one might be a bit more of a philosophical restructuring of your homelab than a
purely NVMe change, but if you're still running your applications on several VMs in Proxmox,
you might want to consider a separate, high-performance cluster using something like
Kubernetes. This can be a big change, but is a great, high-performance way to run a lot of
smaller, containerized services like DNS or DHCP servers, and is something that can really
take advantage of the fast, random read storage an NVMe drive provides. This does rely on
you having several nodes available, whether they're as small as a Raspberry Pi or several
full-sized boxes (though you might have difficulty connecting most SSDs to a Pi cluster.)
Whatever the size of your cluster though, it's still a fun project to set up and experiment with.

4/5

Now you don't need to do this entirely with a reconstruction of how you run your applications,
you could also set up a clustered storage solution like Ceph or GlusterFS to offer an ultra-
fast, distributed storage backend across several nodes in your homelab (this is also great for
a Kubernetes storage backend).

Working with filesystems is a great learning experience

Now some of the options above might seem like tricky endeavors for a minor performance
uplift, and in truth some of them are. But a lot of the value of having a homelab in the first
place, let alone experimenting with it as you should, is that there's something to learn there.
The easy option is simply to run a few VMs from your SSD, and you'll see a very significant
performance improvement from doing that, but if you're willing to get a bit further outside the
box, there are some fun projects to do that are a bit more advanced (especially if you've got
a NAS).

5/5

