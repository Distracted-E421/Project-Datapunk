Introducing Arduino cores with ZephyrOS (beta): take
your embedded development to the next level

blog.arduino.cc/2024/12/05/introducing-arduino-cores-with-zephyros-beta-take-your-embedded-development-to-the-

next-level

December 5, 2024

Last July, when we announced the beginning of the transition from Mbed to Zephyr, we
promised to release the first beta by the end of 2024. Today, we are excited to announce the
first release of Arduino cores with ZephyrOS in beta!

ZephyrOS is an open-source, real-time operating system (RTOS) designed for low-power,
resource-constrained devices. We are transitioning Arduino cores to ZephyrOS to ensure
continued support and innovation for developers. This change follows ARM’s deprecation of
MbedOS, which has historically powered some of our cores. By adopting ZephyrOS, we are
introducing a more modern, scalable, and feature-rich RTOS that aligns with the evolving
needs of the embedded development community. This ensures that Arduino users have
access to a robust, actively maintained platform for creating advanced applications.

With this brand new beta program, we invite our community to explore, test, and contribute to
this significant new development in Arduino’s evolution – one that will allow old and new
Arduino users all around the world to continue using the language and libraries they know
and love for many years to come.

What is ZephyrOS?

ZephyrOS is a state-of-the-art RTOS designed to enable advanced embedded systems. It is
modular, scalable, and supports multiple hardware architectures, making it an excellent
choice for the next generation of Arduino projects.

Its key features include:

Real-time performance: Build responsive applications requiring precise timing.
Flexibility: Customize and scale the system to your specific needs.
Extensibility: Benefit from a rich ecosystem of libraries and subsystems.
Community-driven innovation: Collaborate with a vibrant open-source community.

What’s new in this core?

The Arduino core for ZephyrOS brings significant changes to how Arduino sketches are built
and executed. However, the integration between Arduino core and ZephyrOS operates
seamlessly under the hood, providing advanced RTOS capabilities like real-time scheduling

1/2

and multitasking, while keeping the development process as straightforward as ever. This
means you can enjoy the best of both worlds: the ease of Arduino and the power of a
modern, robust RTOS.

Dynamic sketch loading: Sketches are compiled as ELF files and dynamically loaded
by a precompiled Zephyr-based firmware.
Zephyr subsystems: Leverage features like threading, inter-process communication,
and real-time scheduling.
Fast compiling: Since only a thin layer of user code and libraries are compiled, while
the rest of the ZephyrOS is already binary, compilation is faster and resulting binary
files are smaller.

How to get started

Ready to dive into the future of Arduino development with ZephyrOS? Head over to our
repository for comprehensive installation instructions, troubleshooting tips, and detailed
technical documentation.

Contribute to the beta!

This is your opportunity to shape the future of Arduino development! We welcome feedback,
bug reports, and contributions to the core. Visit the GitHub Issues page to report bugs or
suggest features. Your feedback will play a critical role in refining this integration and
unlocking new possibilities for embedded systems.

Visit theArduinoCore-Zephyr GitHub repository today and start exploring this exciting
new platform!

2/2

