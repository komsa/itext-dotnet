using NUnit.Framework;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

[assembly: AssemblyTitle("iText.Pdfua.Tests")]
[assembly: AssemblyDescription("")]
[assembly: AssemblyConfiguration("")]

[assembly: ComVisible(false)]

[assembly: Guid("f542854e-7f6b-4207-b6ca-004a5d266e65")]

[assembly: Parallelizable(ParallelScope.ContextMask)]

#if !NETSTANDARD2_0
[assembly: NUnit.Framework.Timeout(300000)]
#endif
