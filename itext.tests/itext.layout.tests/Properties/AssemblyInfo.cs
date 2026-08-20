using NUnit.Framework;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;

[assembly: AssemblyTitle("iText.Layout.Tests")]
[assembly: AssemblyDescription("")]
[assembly: AssemblyConfiguration("")]

[assembly: ComVisible(false)]

[assembly: Guid("9ad347a8-ea5b-462b-810c-998f04471bb7")]

[assembly: Parallelizable(ParallelScope.ContextMask)]

#if !NETSTANDARD2_0
[assembly: NUnit.Framework.Timeout(600000)]
#endif
