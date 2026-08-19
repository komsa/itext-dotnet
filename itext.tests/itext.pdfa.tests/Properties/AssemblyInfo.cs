using NUnit.Framework;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

[assembly: AssemblyTitle("iText.Pdfa.Tests")]
[assembly: AssemblyDescription("")]
[assembly: AssemblyConfiguration("")]

[assembly: ComVisible(false)]

[assembly: Guid("b7c0e021-71ac-4c97-9a51-8356f1bd53c7")]

[assembly: Parallelizable(ParallelScope.ContextMask)]

#if !NETSTANDARD2_0
[assembly: NUnit.Framework.Timeout(300000)]
#endif
