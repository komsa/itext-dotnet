using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using NUnit.Framework;

[assembly: AssemblyTitle("iText.WebP-Image-Support.Tests")]
[assembly: AssemblyDescription("")]
[assembly: AssemblyConfiguration("")]

[assembly: ComVisible(false)]

[assembly: Guid("23858C29-C259-4881-A81F-EB57487DB43D")]

[assembly: Parallelizable(ParallelScope.ContextMask)]

#if !NETSTANDARD2_0
[assembly: NUnit.Framework.Timeout(300000)]
#endif
