Building an AMD Ryzen PC can be a nightmare for a first-
time builder, and here's what you need to get right

xda-developers.com/building-amd-ryzen-pc-first-time

December 7, 2024

By  Adam Conway
Published Dec 7, 2024

I've built a couple of Ryzen-based PCs at this point, with my most recent putting the AMD
Ryzen 7 9800X3D at its core. In doing so, I remembered just how much of a nuisance Ryzen
machines can be to build, and while it's not difficult, you need to be especially careful about
how you build it. While there are optimal ways to build a PC, typically you can suboptimally
build a PC with an Intel CPU and not face immediate problems.

With Ryzen, that isn't quite the case, and most of it comes down to memory. Because of how
Ryzen works with its Infinity Fabric, your RAM matters a huge amount depending on what
you're building. Not only do you need to be careful about what RAM you get for your
motherboard (most motherboard manufacturers will publish a list of supported RAM), but you
need to be careful about its positioning, too.

Memory is the most important part of building a new Ryzen PC

Everything else is trivial in comparison

First and foremost, your first boot with a Ryzen PC can take a few minutes longer than you
would expect, and that's because your PC has to do a thing called "memory training." This
process essentially runs through a checklist to ensure that your RAM works correctly with
your CPU, and tunes memory timings and voltage levels for stability. This includes
synchronizing your CPU with the Infinity Fabric Clock, or FCLK.

FCLK is the first pitfall that you could run into as a first-time Ryzen builder. Ryzen CPUs are
typically two CPUs stitched together, and the chiplets with the cores are called Core
Complex Dies (or CCDs). A Core Complex (CCX) is a cluster of cores and can contain two,
four, or eight cores, has its own L3 cache, and works with other CCXs in the same CPU. To
simplify it further, an eight-core AMD CPU might have a CCD with two four-core CCXs.

AMD uses Infinity Fabric to facilitate communication between these two CCXs. You want to
make sure your RAM speed is matched to your FCLK, as if they don't match, it can
"decouple" which will increase latency. When a core in a CCX needs to get data from another

1/3

core in the other CCX, it has to go through the Infinity Fabric connection, or when it needs to
get data from RAM. Your BIOS will typically handle this for you once you set FCLK in the
BIOS to auto, though you may need to manually tweak this if your RAM is too fast.

To be clear, too, matching your RAM speed doesn't mean matching your FCLK to your RAM
MHz. If you have 3600 MHz RAM, you need to set your FCLK to 1800 MHz, as RAM Is DDR,
or Double-Data Rate.

On top of that, you need to make sure your RAM Is both supported by your motherboard,
and in the right slots too. Plus, with high-speed RAM, your motherboard might not even
support running it at its advertised frequency if you have four sticks in your PC.

Finally, if you want to use dual-channel RAM, you'll need to put your RAM sticks into A2 and
B2, and with one stick of RAM, you typically need to put it in A2. Refer to your motherboard's
manual for booting it correctly, as your PC will likely fail to boot with the RAM sticks in the
wrong slots. This isn't always clear to people who are used to Intel, where you can normally
place your RAM in any slot and it will at least boot, even if it's not optimal.

Don't forget to enable Precision Boost Overdrive (PBO) and
DOCP/EXPO

Make everything as fast as possible

For a quick primer on PBO, it's a feature on AMD's Ryzen CPUs that dynamically adjusts the
power limit, voltage, and clock speeds to increase performance. It changes the PPT
(Package Power Tracking), TDC (Thermal Design Current), and EDC (Electrical Design

2/3

Current) limits of your Ryzen CPU based on a few simple inputs to deliver extra performance
without the need for manual overclocking, and you can simply enable it in your BIOS.

On top of that, enabling XMP/DOCP/EXPO will boost your RAM speed to match its
advertised speeds. The default JEDEC profiles for RAM are pretty conservative and easily
surpassed by the speeds supported by most motherboard and CPU combinations. Without
enabling DOCP or EXPO, you're not using the hardware you bought to its full potential.

As already mentioned, Ryzen can be quite sensitive to RAM, so you should play around with
those settings first to ensure that your PC works completely with them. We suggest running a
tool like Memtest to ensure that things are stable, but even if you don't, you'll probably
quickly find out when you do any intensive tasks on your PC.

As you can see, the most important parts about Ryzen to get right all relate to memory. While
PBO and DOCP/EXPO are about improving your speeds, you can even fail to boot for the
first time when you build your PC if you don't get it right. There are a lot of common pitfalls,
so pay extra care when building your Ryzen PC for the first time.

.

3/3

